#!/usr/bin/env python
"""
Scraper: Liberum Ratings – Classificações de risco detalhadas
Fonte:   https://sitev2-api.liberumratings.com.br/getRatings
Saída:   data/liberum_ratings.csv
"""

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.base import BaseScraper
from scripts.utils import print_done, print_fail, print_start

BASE_API_URL = "https://sitev2-api.liberumratings.com.br"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Origin": "https://www.liberumratings.com.br",
    "Referer": "https://www.liberumratings.com.br/",
    "Accept": "application/json, text/plain, */*",
}

CABECALHO = [
    "dt_captura",
    "no_emissor",
    "link",
    "no_tipo_rating",
    "de_rating_br",
    "dt_acao_rating",
    "de_acao_rating",
    "de_outlook",
    "de_classe",
    "de_escala",
]


class LiberumRatingsScraper(BaseScraper):
    name = "liberum_ratings"
    group = "ratings"
    enabled = True
    phase = 1
    chaves_dedup = ["link", "de_classe", "de_escala", "de_rating_br"]
    accumulate = True

    # Catálogo de Metadados
    title = "Liberum — Ratings"
    description = (
        "Ratings de crédito de longo e curto prazo e perspectivas atribuídas pela Liberum Ratings no Brasil."
    )
    icon = "L"
    icon_class = "icon-liberum"
    badge = "Diário"
    badge_class = "badge-daily"
    tags = ["ratings", "liberum", "emissores"]
    source = "Liberum"

    def fetch(self) -> pd.DataFrame:
        from curl_cffi import requests

        self.logger.info("Iniciando busca de ratings Liberum...")
        print_start("Acessando API Liberum Ratings para listar classificações...")

        rows = []
        page = 1
        items_per_page = 40  # Reduzido para evitar timeouts
        total_pages = 1
        max_retries = 3

        while page <= total_pages:
            self.logger.info(f"Buscando página {page}/{total_pages}...")
            params = {
                "page": page,
                "itemsPerPage": items_per_page,
                "category": "",
                "lastro": "",
                "quota": "",
                "ratingFilter": "",
                "instituitionName": "",
            }

            data_json = None
            for attempt in range(max_retries):
                try:
                    resp = requests.get(
                        f"{BASE_API_URL}/getRatings",
                        params=params,
                        headers=HEADERS,
                        impersonate="chrome",
                        timeout=45,
                    )
                    resp.raise_for_status()
                    data_json = resp.json()
                    break
                except Exception as e:
                    self.logger.warning(f"Tentativa {attempt + 1} falhou para a página {page}: {e}")
                    if attempt == max_retries - 1:
                        self.logger.error(f"Erro persistente na página {page}: {e}")
                        print_fail(f"Erro ao acessar API Liberum na página {page}: {e}")
                        break
                    time.sleep(2**attempt)

            if data_json is None:
                break

            if page == 1:
                total_pages = data_json.get("pages", 1)
                self.logger.info(f"Total de páginas a buscar: {total_pages}")

            items = data_json.get("data", [])
            if not items:
                self.logger.info("Página vazia. Fim da paginação.")
                break

            for item in items:
                nome = (item.get("ativo") or "").strip()
                id_relatorio = item.get("id_relatorio")
                categoria = (item.get("categoria") or "").strip()
                data_classificacao = item.get("data_classificacao") or ""
                dt_acao_rating = data_classificacao[:10] if len(data_classificacao) >= 10 else ""

                if not nome or not id_relatorio:
                    continue

                link_detalhes = f"https://www.liberumratings.com.br/detalhes-ativo/{id_relatorio}"
                interno = item.get("interno") or []

                for sub in interno:
                    classe = (sub.get("classe") or "").strip()
                    acao = (sub.get("acao") or "").strip()
                    nota = (sub.get("nota") or "").strip()
                    escala = (sub.get("escala") or "").strip()
                    perspectiva = (sub.get("perspectiva") or "").strip()

                    if not nota:
                        continue

                    rows.append(
                        {
                            "no_emissor": nome,
                            "link": link_detalhes,
                            "no_tipo_rating": categoria,
                            "de_rating_br": nota,
                            "dt_acao_rating": dt_acao_rating,
                            "de_acao_rating": acao,
                            "de_outlook": perspectiva,
                            "de_classe": classe,
                            "de_escala": escala,
                        }
                    )

            page += 1
            time.sleep(0.3)

        df = pd.DataFrame(rows)
        self.logger.info(f"Total de {len(df)} ratings extraídos da Liberum.")
        print_done(f"{len(df)} ratings encontrados")

        if not df.empty:
            colunas = [c for c in CABECALHO if c in df.columns]
            return df[colunas]
        return df


if __name__ == "__main__":
    scraper = LiberumRatingsScraper()
    scraper.run()
