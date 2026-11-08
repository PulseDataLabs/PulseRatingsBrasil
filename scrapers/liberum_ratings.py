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
        from scrapers.utils.liberum_helper import get_liberum_raw_items

        self.logger.info("Iniciando busca de ratings Liberum...")
        print_start("Acessando API Liberum Ratings para listar classificações...")

        items = get_liberum_raw_items(self.logger)
        rows = []

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
