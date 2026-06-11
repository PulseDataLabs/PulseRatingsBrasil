#!/usr/bin/env python
# coding: utf-8
"""
Scraper: Austin Rating – Emissores com rating no Brasil
Fonte:   https://www.austin.com.br/Ratings-Explorer.html
Saída:   data/austin_emissores.csv
"""
import os
import sys
import datetime
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.base import BaseScraper
from scripts.utils import print_done, print_info, print_warn, print_start, print_fail

BASE_URL = "https://www.austin.com.br"
EXPLORER_URL = f"{BASE_URL}/Ratings-Explorer.html"


class AustinEmissoresScraper(BaseScraper):
    name = "austin_emissores"
    group = "ratings"
    enabled = True
    phase = 1
    chaves_dedup = ["link"]
    accumulate = False

    # Catálogo de Metadados
    title = "Austin — Emissores"
    description = "Emissores com rating de crédito ativo ou histórico de classificação regulatória pela Austin Rating no Brasil."
    icon = "A"
    icon_class = "icon-austin"
    badge = "Diário"
    badge_class = "badge-daily"
    tags = ["ratings", "austin", "emissores"]
    source = "Austin"

    def fetch(self) -> pd.DataFrame:
        from curl_cffi import requests

        self.logger.info(f"Acessando {EXPLORER_URL}...")
        print_start("Acessando Austin Ratings Explorer...")
        try:
            # Usa curl_cffi para contornar qualquer barreira básica do servidor
            resp = requests.get(EXPLORER_URL, impersonate="chrome", timeout=60)
            resp.raise_for_status()
        except Exception as e:
            self.logger.error(f"Erro ao acessar Austin Rating: {e}")
            print_fail(f"Erro ao acessar Austin Rating: {e}")
            return pd.DataFrame()

        print_done("Página carregada")
        self.logger.info("Processando HTML e extraindo emissores...")
        print_start("Processando emissores...")

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Encontra todos os links com name="RatingName" que levam à página de detalhes/histórico
        links = soup.find_all("a", attrs={"name": "RatingName"}, href=True)
        self.logger.info(f"Encontrados {len(links)} links de ratings no HTML.")

        emissores = {}
        for link in links:
            nome = link.get_text(strip=True)
            href = link["href"].strip()
            
            if not nome or not href:
                continue
            
            # Tenta encontrar o setor na segunda coluna do tr
            tr = link.find_parent("tr")
            setor = ""
            if tr:
                tds = tr.find_all("td")
                if len(tds) > 1:
                    setor = tds[1].get_text(strip=True).replace("\xa0", " ")

            # Reconstrói link absoluto
            if href.startswith("/"):
                link_completo = BASE_URL + href
            elif not href.startswith("http"):
                link_completo = BASE_URL + "/" + href
            else:
                link_completo = href
                
            # Deduplica por link, armazenando nome, setor e link
            if link_completo not in emissores:
                emissores[link_completo] = {
                    "no_emissor": nome,
                    "no_setor": setor,
                    "link": link_completo
                }

        rows = list(emissores.values())
        
        df = pd.DataFrame(rows)
        self.logger.info(f"Total de {len(df)} emissores únicos extraídos.")
        print_done(f"{len(df)} emissores encontrados")
        
        return df


if __name__ == "__main__":
    scraper = AustinEmissoresScraper()
    scraper.run()
