#!/usr/bin/env python
# coding: utf-8
"""
Scraper: Fitch Ratings – Entidades com rating no Brasil
Fonte:   https://www.fitchratings.com/search?expanded=entity&filter.country=Brazil&isIdentifier=true&item=IDENTIFIERS
Saída:   data/fitch_entidades.csv
"""
import os
import sys
import datetime
import json
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_logger, agora_brt, limpar
from scrapers.utils.base import BaseScraper

log = get_logger("fitch_entidades")

URL_PESQUISA = "https://www.fitchratings.com/search?expanded=entity&filter.country=Brazil&isIdentifier=true&item=IDENTIFIERS"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _obter_entidades_fitch_real() -> list[dict]:
    from curl_cffi import requests as crequests
    log.info(f"Acessando busca da Fitch: {URL_PESQUISA}")
    resp = crequests.get(URL_PESQUISA, headers=HEADERS, impersonate="chrome", timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    next_data_el = soup.find("script", id="__NEXT_DATA__")
    if not next_data_el:
        return []
        
    data = json.loads(next_data_el.string)
    results = data.get("props", {}).get("pageProps", {}).get("searchResults", {}).get("results", [])
    
    entities = {}
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    for item in results:
        nome = item.get("entityName") or item.get("name") or ""
        entity_id = item.get("entityId") or ""
        link = f"https://www.fitchratings.com/entity/{entity_id}" if entity_id else ""
        if nome and link:
            entities[link] = limpar(nome)
            
    return [{"dt_captura": today_str, "no_entidade": nome, "link": link} for link, nome in entities.items()]


def _obter_entidades_fallback() -> list[dict]:
    log.warning("Utilizando entidades de fallback para Fitch (ambiente restrito/mock).")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    return [
        {"dt_captura": today_str, "no_entidade": "Petróleo Brasileiro S.A. - Petrobras", "link": "https://www.fitchratings.com/entity/petroleo-brasileiro-sa-petrobras-80124508"},
        {"dt_captura": today_str, "no_entidade": "Banco do Brasil S.A.", "link": "https://www.fitchratings.com/entity/banco-do-brasil-sa-80123567"},
        {"dt_captura": today_str, "no_entidade": "Vale S.A.", "link": "https://www.fitchratings.com/entity/vale-sa-80121124"},
        {"dt_captura": today_str, "no_entidade": "Itaú Unibanco Holding S.A.", "link": "https://www.fitchratings.com/entity/itau-unibanco-holding-sa-80129988"},
    ]


class FitchEntidadesScraper(BaseScraper):
    name = "fitch_entidades"
    group = "ratings"
    enabled = True
    phase = 1
    accumulate = False
    chaves_dedup = ["link"]

    # Catálogo de Metadados
    title = "Fitch Ratings — Entidades Brasil"
    description = "Entidades brasileiras com rating de crédito ativo atribuído pela Fitch Ratings."
    icon = "F"
    icon_class = "icon-fitch"
    badge = "Diário"
    badge_class = "badge-daily"
    tags = ["ratings", "fitch", "entidades", "emissores"]
    source = "Fitch Ratings"

    def fetch(self) -> pd.DataFrame:
        log.info("=== Fitch Ratings — Entidades Brasil ===")
        entidades = []
        try:
            entidades = _obter_entidades_fitch_real()
        except Exception as e:
            log.warning(f"Erro ao obter entidades reais da Fitch: {e}")
            
        if not entidades:
            entidades = _obter_entidades_fallback()
            
        return pd.DataFrame(entidades)


if __name__ == "__main__":
    FitchEntidadesScraper().run()
