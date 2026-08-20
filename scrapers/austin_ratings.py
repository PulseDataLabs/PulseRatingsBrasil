#!/usr/bin/env python
"""
Scraper: Austin Rating – Ratings de emissores brasileiros
Fonte:   Historico-Rating em https://www.austin.com.br
Saída:   data/austin_ratings.csv

Carrega a lista de emissores gerada por austin_emissores.csv e
acessa de forma concorrente a página de histórico de cada um.
"""

import datetime
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.base import BaseScraper
from scripts.utils import (
    IS_TTY,
    dim,
    print_done,
    print_fail,
    print_start,
    print_warn,
    progress_bar,
)
from utils.paths import get_data_dir

BASE_URL = "https://www.austin.com.br"


def parse_austin_date(date_str: str) -> str:
    """Converte datas de DD/MM/YYYY para YYYY-MM-DD."""
    if not date_str:
        return ""
    date_str = date_str.strip()
    parts = date_str.split("/")
    if len(parts) == 3:
        day, month, year = parts
        return f"{year}-{month}-{day}"
    return date_str


def scrape_emissor_history(emissor_info: dict) -> list[dict]:
    """Acessa a página de histórico e parseia a tabela de ratings."""
    from curl_cffi import requests

    nome = emissor_info["no_emissor"]
    setor = emissor_info["no_setor"]
    link = emissor_info["link"]

    try:
        resp = requests.get(link, impersonate="chrome", timeout=30)
        if resp.status_code != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", id="tableRatingList")
    if not table:
        return []

    tbody = table.find("tbody")
    if not tbody:
        return []

    rows = []
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue

        dt_raw = tds[0].get_text(strip=True)
        acao = tds[1].get_text(strip=True)
        rating_cp = tds[2].get_text(strip=True).replace("\xa0", "").strip()
        rating_lp = tds[3].get_text(strip=True).replace("\xa0", "").strip()
        outlook = tds[4].get_text(strip=True).replace("\xa0", "").strip()

        # Link do relatório (opcional, sexta coluna)
        report_link = ""
        if len(tds) > 5:
            a_rel = tds[5].find("a", href=True)
            if a_rel:
                href = a_rel["href"].strip()
                if href.startswith("/"):
                    report_link = BASE_URL + href
                elif not href.startswith("http"):
                    report_link = BASE_URL + "/" + href
                else:
                    report_link = href

        # Data de ação convertida
        dt_acao = parse_austin_date(dt_raw)

        # Escolhe a principal nota de rating (privilegia Longo Prazo, mas usa Curto Prazo se for vazio)
        rating_principal = rating_lp if rating_lp else rating_cp

        rows.append(
            {
                "no_emissor": nome,
                "link": link,
                "no_tipo_rating": setor,
                "de_rating_br": rating_principal,
                "de_rating_cp": rating_cp,
                "de_rating_lp": rating_lp,
                "dt_acao_rating": dt_acao,
                "de_acao_rating": acao,
                "de_outlook": outlook,
                "link_relatorio": report_link,
            }
        )

    return rows


class AustinRatingsScraper(BaseScraper):
    name = "austin_ratings"
    group = "ratings"
    enabled = True
    phase = 2
    chaves_dedup = [
        "link",
        "no_tipo_rating",
        "de_rating_br",
        "dt_acao_rating",
    ]
    accumulate = True

    # Catálogo de Metadados
    title = "Austin — Ratings"
    description = "Histórico de ratings de crédito atribuídos pela Austin Rating a emissores e emissões estruturadas (FIDCs, CRIs, debêntures e bancos) no Brasil."
    icon = "A"
    icon_class = "icon-austin"
    badge = ""
    badge_class = ""
    tags = ["ratings", "austin", "emissores"]
    source = "Austin"

    def fetch(self) -> pd.DataFrame:
        emissores_csv = get_data_dir() / "austin_emissores.csv"
        if not emissores_csv.exists():
            self.logger.warning(
                f"Arquivo de emissores não encontrado: {emissores_csv}. Execute austin_emissores.py primeiro."
            )
            print_fail("CSV de emissores não encontrado")
            return pd.DataFrame()

        df_emissores = pd.read_csv(emissores_csv)
        if "link" not in df_emissores.columns:
            self.logger.warning("Coluna 'link' não encontrada no CSV de emissores.")
            print_fail("Coluna 'link' não encontrada no CSV")
            return pd.DataFrame()

        # Converte DataFrame em lista de dicionários para processamento
        emissores_list = df_emissores.to_dict(orient="records")
        total = len(emissores_list)

        print_start(f"Processando {total} emissores da Austin Rating concorrentemente...")

        all_ratings = []
        completed = 0

        # Dispara conexões concorrentes para acelerar o processo
        with ThreadPoolExecutor(max_workers=15) as executor:
            future_to_emissor = {executor.submit(scrape_emissor_history, em): em for em in emissores_list}

            for future in as_completed(future_to_emissor):
                em = future_to_emissor[future]
                nome = em.get("no_emissor", "")
                completed += 1

                # Atualiza a barra de progresso no terminal
                bar = progress_bar(completed, total)
                print(f"  {bar}  {dim(nome[:72])}", end="\r" if IS_TTY else "\n")

                try:
                    result = future.result()
                    if result:
                        all_ratings.extend(result)
                except Exception as e:
                    self.logger.warning(f"Erro ao processar emissor {nome}: {e}")

        if not all_ratings:
            self.logger.warning("Nenhum rating capturado.")
            print_warn("Nenhum rating capturado")
            return pd.DataFrame()

        df = pd.DataFrame(all_ratings)
        df.insert(0, "dt_captura", datetime.date.today().strftime("%Y-%m-%d"))

        # Ordenação de colunas padrão
        col_order = [
            "dt_captura",
            "no_emissor",
            "link",
            "no_tipo_rating",
            "de_rating_br",
            "de_rating_cp",
            "de_rating_lp",
            "dt_acao_rating",
            "de_acao_rating",
            "de_outlook",
            "link_relatorio",
        ]
        df = df[[c for c in col_order if c in df.columns]]

        print_done(f"{len(df)} ratings capturados de {completed} emissores")
        return df


if __name__ == "__main__":
    scraper = AustinRatingsScraper()
    scraper.run()
