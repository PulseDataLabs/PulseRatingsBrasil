#!/usr/bin/env python
"""
Scraper: Liberum Ratings – Emissores com rating no Brasil
Fonte:   https://sitev2-api.liberumratings.com.br/getRatings
Saída:   data/liberum_emissores.csv
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


class LiberumEmissoresScraper(BaseScraper):
    name = "liberum_emissores"
    group = "ratings"
    enabled = True
    phase = 1
    chaves_dedup = ["link"]
    accumulate = False

    # Catálogo de Metadados
    title = "Liberum — Emissores"
    description = "Emissores com classificação de risco ativa ou monitorada pela Liberum Ratings no Brasil."
    icon = "L"
    icon_class = "icon-liberum"
    badge = "Diário"
    badge_class = "badge-daily"
    tags = ["ratings", "liberum", "emissores"]
    source = "Liberum"

    def fetch(self) -> pd.DataFrame:
        from scrapers.utils.liberum_helper import get_liberum_raw_items

        self.logger.info("Iniciando busca de emissores Liberum...")
        print_start("Acessando API Liberum Ratings para listar emissores...")

        items = get_liberum_raw_items(self.logger)
        emissores = {}

        for item in items:
            nome = (item.get("ativo") or "").strip()
            id_relatorio = item.get("id_relatorio")
            categoria = (item.get("categoria") or "").strip()

            if not nome or not id_relatorio:
                continue

            link_detalhes = f"https://www.liberumratings.com.br/detalhes-ativo/{id_relatorio}"

            if link_detalhes not in emissores:
                emissores[link_detalhes] = {
                    "no_emissor": nome,
                    "no_setor": categoria,
                    "link": link_detalhes,
                }

        rows = list(emissores.values())
        df = pd.DataFrame(rows)
        self.logger.info(f"Total de {len(df)} emissores únicos extraídos da Liberum.")
        print_done(f"{len(df)} emissores encontrados")

        return df


if __name__ == "__main__":
    scraper = LiberumEmissoresScraper()
    scraper.run()
