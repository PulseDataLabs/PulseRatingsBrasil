#!/usr/bin/env python
# coding: utf-8
"""
Scraper: Moody's – Lista de Classificações Vigentes (Brasil)
Fonte:   https://moodyslocal.com.br/
Saída:   data/moodys_ratings.csv

A página disponibiliza um link direto para download do Excel de ratings.
O scraper utiliza get_moodys_raw_data para download otimizado com cache
e parsing ultrarrápido via streaming XML.
"""
import os
import sys
import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.utils.base import BaseScraper
from scripts.utils import print_done, print_start, print_fail

RENAME_MAP = {
    "Setor": "no_setor",
    "Emissor": "no_emissor",
    "Produto": "no_tipo_rating",
    "Instrumento": "de_instrumento",
    "Objeto": "de_objeto",
    "Rating / Avaliação": "de_rating_br",
    "Perspectiva": "de_outlook",
    "Última data de atualização": "dt_rating",
}


class MoodysRatingsScraper(BaseScraper):
    name = "moodys_ratings"
    group = "ratings"
    enabled = True
    phase = 2
    accumulate = True

    # Catálogo de Metadados
    title = "Moody's — Ratings"
    description = "Ratings de crédito atribuídos pela Moody's Local a emissores corporativos, financeiros, de financiamento estruturado e públicos no Brasil."
    icon = "M"
    icon_class = "icon-moodys"
    badge = ""
    badge_class = ""
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
            self.logger.warning("Nenhum dado extraído do Excel da Moody's.")
            return pd.DataFrame()

        self.logger.info(f"Total de {len(data_rows)} ratings extraídos.")
        print_done(f"{len(data_rows)} ratings extraídos")

        df = pd.DataFrame(data_rows, columns=headers)
        df["dh_atu_arquivo"] = file_date or datetime.date.today().strftime("%Y-%m-%d")
        df.rename(columns=RENAME_MAP, inplace=True)

        # Filtra apenas as colunas configuradas em RENAME_MAP mais a data de atualização
        keep_cols = list(RENAME_MAP.values()) + ["dh_atu_arquivo"]
        df = df[[c for c in keep_cols if c in df.columns]]

        return df


if __name__ == "__main__":
    scraper = MoodysRatingsScraper()
    scraper.run()
