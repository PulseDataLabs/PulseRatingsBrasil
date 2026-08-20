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
        from curl_cffi import requests

        self.logger.info("Iniciando busca de emissores Liberum...")
        print_start("Acessando API Liberum Ratings para listar emissores...")

        emissores = {}
        page = 1
        items_per_page = 40  # Reduzido de 100 para 40 para evitar timeouts
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
                        timeout=45,  # 45s de timeout
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
                # Interrompe o loop se não conseguimos recuperar a página mesmo após retentativas
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

                if not nome or not id_relatorio:
                    continue

                link_detalhes = f"https://www.liberumratings.com.br/detalhes-ativo/{id_relatorio}"

                if link_detalhes not in emissores:
                    emissores[link_detalhes] = {
                        "no_emissor": nome,
                        "no_setor": categoria,
                        "link": link_detalhes,
                    }

            page += 1
            time.sleep(0.3)

        rows = list(emissores.values())
        df = pd.DataFrame(rows)
        self.logger.info(f"Total de {len(df)} emissores únicos extraídos da Liberum.")
        print_done(f"{len(df)} emissores encontrados")

        return df


if __name__ == "__main__":
    scraper = LiberumEmissoresScraper()
    scraper.run()
