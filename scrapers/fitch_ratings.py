#!/usr/bin/env python
# coding: utf-8
"""
Scraper: Fitch Ratings – Ratings de emissores brasileiros
Fonte:   GraphQL API — https://api.fitchratings.com
Saída:   data/fitch_ratings.csv
"""
import sys
import datetime
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_logger, agora_brt, limpar
from scrapers.utils.base import BaseScraper

log = get_logger("fitch_ratings")

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
            ratings {
                ratingCode
                ratingTypeDescription
                ratingEffectiveDate
                ratingActionDescription
                ratingAlertDescription
            }
        }
    }
}
"""

CABECALHO = [
    "dt_captura",
    "no_entidade",
    "link",
    "Tipo de Rating",
    "Rating",
    "Data da Ação de Rating",
    "Ação de Rating",
    "CreditWatch/ Perspectiva",
]

PAGE_SIZE = 100
MAX_PAGES = 20  # Segurança: máximo 2000 emissores


def _formatar_data(iso_str: str) -> str:
    """Converte ISO datetime (2026-06-03T15:33:00.000Z) para YYYY-MM-DD."""
    if not iso_str:
        return ""
    try:
        return iso_str[:10]  # Pega apenas YYYY-MM-DD
    except Exception:
        return str(iso_str)


def _obter_ratings_via_api() -> list[dict]:
    """Obtém todos os ratings de emissores brasileiros da Fitch via GraphQL API."""
    from curl_cffi import requests as crequests

    dt_captura, _ = agora_brt()
    rows = []
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
            log.info(f"Total de emissores brasileiros na Fitch: {total}")

        entity_hits = search.get("entity", [])
        if not entity_hits:
            log.info("Nenhum emissor retornado nesta página. Fim da paginação.")
            break

        emissores_com_rating = 0
        for hit in entity_hits:
            nome = limpar(hit.get("name", "").strip())
            permalink = hit.get("permalink", "").strip()
            link = f"https://www.fitchratings.com/entity/{permalink}" if permalink else ""

            if not nome or not link:
                continue

            ratings = hit.get("ratings") or []
            if not ratings:
                continue

            emissores_com_rating += 1
            for r in ratings:
                alert_desc = r.get("ratingAlertDescription") or ""
                if alert_desc == "-":
                    alert_desc = ""

                rows.append({
                    "dt_captura": dt_captura,
                    "no_entidade": nome,
                    "link": link,
                    "Tipo de Rating": limpar(r.get("ratingTypeDescription") or ""),
                    "Rating": limpar(r.get("ratingCode") or ""),
                    "Data da Ação de Rating": _formatar_data(r.get("ratingEffectiveDate") or ""),
                    "Ação de Rating": limpar(r.get("ratingActionDescription") or ""),
                    "CreditWatch/ Perspectiva": limpar(alert_desc),
                })

        log.info(
            f"  Página {page}: {len(entity_hits)} emissores, "
            f"{emissores_com_rating} com ratings (acumulado: {len(rows)} ratings)"
        )

        offset += PAGE_SIZE
        if offset >= total:
            log.info("Todos os emissores foram processados.")
            break

        # Pausa entre requisições para evitar rate-limiting
        time.sleep(1)

    log.info(f"Total de ratings capturados: {len(rows)}")
    return rows


class FitchRatingsScraper(BaseScraper):
    name = "fitch_ratings"
    group = "ratings"
    enabled = True
    phase = 2
    accumulate = True
    chaves_dedup = ["link", "Tipo de Rating"]

    # Catálogo de Metadados
    title = "Fitch — Ratings"
    description = (
        "Ratings de crédito de longo e curto prazo atribuídos pela Fitch Ratings "
        "a emissores corporativos, financeiros e soberanos no Brasil."
    )
    icon = "F"
    icon_class = "icon-fitch"
    badge = ""
    badge_class = ""
    tags = ["ratings", "fitch", "emissores"]
    source = "Fitch"

    def fetch(self) -> pd.DataFrame:
        log.info("=== Fitch Ratings — Emissores Brasil ===")

        todos = []
        try:
            todos = _obter_ratings_via_api()
        except Exception as e:
            log.error(f"Erro ao obter ratings da Fitch: {e}", exc_info=True)

        if not todos:
            log.warning("Nenhum rating obtido da Fitch.")

        df = pd.DataFrame(todos)
        if not df.empty:
            colunas = [c for c in CABECALHO if c in df.columns]
            return df[colunas]
        return df


if __name__ == "__main__":
    FitchRatingsScraper().run()
