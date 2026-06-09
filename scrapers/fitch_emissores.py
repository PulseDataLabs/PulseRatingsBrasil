#!/usr/bin/env python
# coding: utf-8
"""
Scraper: Fitch Ratings – Emissores com rating no Brasil
Fonte:   GraphQL API — https://api.fitchratings.com
Saída:   data/fitch_emissores.csv
"""
import os
import sys
import datetime
import json
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_logger, agora_brt, limpar
from scrapers.utils.base import BaseScraper
from scripts.utils import print_done, print_info, print_warn, print_start

log = get_logger("fitch_emissores")

API_URL = "https://api.fitchratings.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://www.fitchratings.com",
    "Referer": "https://www.fitchratings.com/search",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

GQL_QUERY = """
query {
    search(term: "", filter: {country: "Brazil"}, limit: %d, offset: %d) {
        totalEntityHits
        entity {
            name
            permalink
        }
    }
}
"""

PAGE_SIZE = 100
MAX_PAGES = 20  # Segurança: máximo 2000 emissores


def _obter_emissores_fitch_real() -> list[dict]:
    """Obtém emissores brasileiras da Fitch via GraphQL API com paginação."""
    from curl_cffi import requests as crequests

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    entities = {}
    offset = 0
    total = None

    for page in range(1, MAX_PAGES + 1):
        query = GQL_QUERY % (PAGE_SIZE, offset)
        payload = {"query": query}

        log.info(f"Requisição GraphQL: offset={offset}, limit={PAGE_SIZE} (página {page})")

        resp = crequests.post(
            API_URL,
            json=payload,
            headers=HEADERS,
            impersonate="chrome",
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if "errors" in data:
            log.error(f"Erro na resposta GraphQL: {data['errors']}")
            break

        search = data.get("data", {}).get("search", {})

        if total is None:
            total = search.get("totalEntityHits", 0)
            log.info(f"Total de emissores brasileiras na Fitch: {total}")
            print_info(f"Total de emissores: {total}", "chart")

        entity_hits = search.get("entity", [])
        if not entity_hits:
            log.info("Nenhum emissor retornado nesta página. Fim da paginação.")
            break

        for hit in entity_hits:
            nome = hit.get("name", "").strip()
            permalink = hit.get("permalink", "").strip()
            if nome and permalink:
                link = f"https://www.fitchratings.com/entity/{permalink}"
                entities[link] = limpar(nome)

        msg = f"Página {page}: {len(entity_hits)} emissores (acumulado: {len(entities)})"
        log.info(f"  {msg}")
        from scripts.utils import progress_bar
        bar = progress_bar(len(entities), total) if total else ""
        print(f"    {bar}")

        offset += PAGE_SIZE
        if offset >= total:
            log.info("Todas as emissores foram obtidas.")
            print_done("Todas as páginas obtidas")
            break

        time.sleep(1)

    log.info(f"Total de emissores únicas capturadas: {len(entities)}")
    print_done(f"{len(entities)} emissores únicas capturadas")
    return [
        {"dt_captura": today_str, "no_emissor": nome, "link": link}
        for link, nome in entities.items()
    ]


class FitchEmissoresScraper(BaseScraper):
    name = "fitch_emissores"
    group = "ratings"
    enabled = True
    phase = 1
    accumulate = False
    chaves_dedup = ["link"]

    # Catálogo de Metadados
    title = "Fitch — Ratings"
    description = "Emissores brasileiros com rating de crédito ativo atribuído pela Fitch Ratings."
    icon = "F"
    icon_class = "icon-fitch"
    badge = "Diário"
    badge_class = "badge-daily"
    tags = ["ratings", "fitch", "emissores"]
    source = "Fitch"

    def fetch(self) -> pd.DataFrame:
        log.info("=== Fitch Ratings — Emissores Brasil ===")
        print_start("Buscando emissores na API GraphQL da Fitch...")
        emissores = []
        try:
            emissores = _obter_emissores_fitch_real()
        except Exception as e:
            log.error(f"Erro ao obter emissores da Fitch: {e}", exc_info=True)
            print_fail(f"Erro ao obter emissores: {e}")

        if not emissores:
            log.warning("Nenhum emissor obtido da Fitch.")
            print_warn("Nenhum emissor obtido")

        return pd.DataFrame(emissores)


if __name__ == "__main__":
    FitchEmissoresScraper().run()
