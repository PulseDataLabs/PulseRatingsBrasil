#!/usr/bin/env python
# coding: utf-8
"""
Scraper: Moody's – Lista de Emissores Vigentes (Brasil)
Fonte:   https://moodyslocal.com.br/
Saída:   data/moodys_emissores.csv
"""
import os
import sys
import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.utils.base import BaseScraper
from scripts.utils import print_done, print_start, print_fail


class MoodysEmissoresScraper(BaseScraper):
    name = "moodys_emissores"
    group = "ratings"
    enabled = True
    phase = 1
    accumulate = False
    chaves_dedup = ["no_emissor"]

    # Catálogo de Metadados
    title = "Moody's — Emissores"
    description = "Lista de emissores (emissores corporativos, financeiros e públicos) com rating vigente pela Moody's no Brasil."
    icon = "M"
    icon_class = "icon-moodys"
    badge = "Diário"
    badge_class = "badge-daily"
    tags = ["ratings", "moodys", "emissores"]
    source = "Moody's"

    def fetch(self) -> pd.DataFrame:
        from scrapers.utils.moodys_helper import get_moodys_raw_data

        print_start("Obtendo dados da Moody's Local...")
        try:
            headers, data_rows, file_date = get_moodys_raw_data(self.logger)
        except Exception as e:
            self.logger.error(f"Erro ao obter dados da Moody's Local: {e}")
            print_fail(f"Erro ao obter dados: {e}")
            return pd.DataFrame()

        if not data_rows or not headers:
            self.logger.warning("Nenhum dado retornado do arquivo da Moody's.")
            return pd.DataFrame()

        df = pd.DataFrame(data_rows, columns=headers)
        df.rename(columns={"Emissor": "no_emissor"}, inplace=True)
        df.drop_duplicates(subset=["no_emissor"], inplace=True)
        
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        df.insert(0, "dt_captura", today_str)
        df["link"] = ""

        # Mantém apenas as colunas unificadas
        df = df[["dt_captura", "no_emissor", "link"]]

        print_done(f"{len(df)} emissores extraídos")
        return df


if __name__ == "__main__":
    MoodysEmissoresScraper().run()
