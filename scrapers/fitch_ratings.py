#!/usr/bin/env python
"""
Scraper: Fitch Ratings – Ratings de emissores brasileiros
Fonte:   GraphQL API — https://api.fitchratings.com
Saída:   data/fitch_ratings.csv
"""

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.base import BaseScraper
from scripts.utils import print_done, print_fail, print_info, print_start, print_warn, progress_bar
from utils import agora_brt, get_logger, limpar

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

GQL_ENTITY_QUERY = """
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

GQL_ISSUE_QUERY = """
query {
    search(term: "", filter: {country: "Brazil"}, limit: %d, offset: %d) {
        totalIssueHits
        issue {
            issueName
            entityName
            permalink
            isin
            maturityDate
            issuer
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
    "no_emissor",
    "link",
    "no_tipo_rating",
    "de_rating_br",
    "dt_acao_rating",
    "de_acao_rating",
    "de_outlook",
    "de_instrumento",
    "de_isin",
]

PAGE_SIZE = 100
MAX_PAGES = 20  # Segurança: máximo 2000 emissores/emissões


def _formatar_data(iso_str: str) -> str:
    """Converte ISO datetime (2026-06-03T15:33:00.000Z) para YYYY-MM-DD."""
    if not iso_str:
        return ""
    try:
        return iso_str[:10]  # Pega apenas YYYY-MM-DD
    except Exception:
        return str(iso_str)


def _obter_ratings_via_api() -> list[dict]:
    """Obtém todos os ratings de emissores e emissões brasileiros da Fitch via GraphQL API."""
    from curl_cffi import requests as crequests

    dt_captura, _ = agora_brt()
    rows = []

    # 1. Obter emissores
    offset = 0
    total = None
    log.info("Buscando ratings de EMISSORES...")
    print_info("Buscando ratings de emissores...", "chart")

    for page in range(1, MAX_PAGES + 1):
        query = GQL_ENTITY_QUERY % (PAGE_SIZE, offset)
        payload = {"query": query}

        log.info(f"Requisição GraphQL Emissores: offset={offset}, limit={PAGE_SIZE} (página {page})")

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
            log.error(f"Erro na resposta GraphQL Emissores: {data['errors']}")
            break

        search = data.get("data", {}).get("search", {})

        if total is None:
            total = search.get("totalEntityHits", 0)
            log.info(f"Total de emissores brasileiros na Fitch: {total}")
            print_info(f"Total de emissores: {total}", "chart")

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

                rows.append(
                    {
                        "dt_captura": dt_captura,
                        "no_emissor": nome,
                        "link": link,
                        "no_tipo_rating": limpar(r.get("ratingTypeDescription") or ""),
                        "de_rating_br": limpar(r.get("ratingCode") or ""),
                        "dt_acao_rating": _formatar_data(r.get("ratingEffectiveDate") or ""),
                        "de_acao_rating": limpar(r.get("ratingActionDescription") or ""),
                        "de_outlook": limpar(alert_desc),
                        "de_instrumento": "",
                        "de_isin": "",
                    }
                )

        log.info(
            f"  Página {page}: {len(entity_hits)} emissores, "
            f"{emissores_com_rating} com ratings (acumulado: {len(rows)} ratings)"
        )
        bar = progress_bar(offset + PAGE_SIZE, total) if total else ""
        print(f"    {bar}")

        offset += PAGE_SIZE
        if offset >= total:
            log.info("Todos os emissores foram processados.")
            break

        time.sleep(1)

    # 2. Obter emissões
    offset = 0
    total = None
    log.info("Buscando ratings de EMISSÕES...")
    print_info("Buscando ratings de emissões...", "chart")

    for page in range(1, MAX_PAGES + 1):
        query = GQL_ISSUE_QUERY % (PAGE_SIZE, offset)
        payload = {"query": query}

        log.info(f"Requisição GraphQL Emissões: offset={offset}, limit={PAGE_SIZE} (página {page})")

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
            log.error(f"Erro na resposta GraphQL Emissões: {data['errors']}")
            break

        search = data.get("data", {}).get("search", {})

        if total is None:
            total = search.get("totalIssueHits", 0)
            log.info(f"Total de emissões brasileiras na Fitch: {total}")
            print_info(f"Total de emissões: {total}", "chart")

        issue_hits = search.get("issue", [])
        if not issue_hits:
            log.info("Nenhuma emissão retornada nesta página. Fim da paginação.")
            break

        emissoes_com_rating = 0
        for hit in issue_hits:
            issue_name = limpar(hit.get("issueName", "").strip())
            entity_name = limpar(hit.get("entityName", "").strip())
            permalink = hit.get("permalink", "").strip()
            link = f"https://www.fitchratings.com/entity/{permalink}" if permalink else ""
            issuer = limpar(hit.get("issuer", "").strip()) or entity_name

            isins_list = hit.get("isin") or []
            de_isin = ", ".join([i for i in isins_list if i])

            if not issue_name or not link:
                continue

            ratings = hit.get("ratings") or []
            if not ratings:
                continue

            emissoes_com_rating += 1
            for r in ratings:
                alert_desc = r.get("ratingAlertDescription") or ""
                if alert_desc == "-":
                    alert_desc = ""

                rows.append(
                    {
                        "dt_captura": dt_captura,
                        "no_emissor": issuer,
                        "link": link,
                        "no_tipo_rating": limpar(r.get("ratingTypeDescription") or ""),
                        "de_rating_br": limpar(r.get("ratingCode") or ""),
                        "dt_acao_rating": _formatar_data(r.get("ratingEffectiveDate") or ""),
                        "de_acao_rating": limpar(r.get("ratingActionDescription") or ""),
                        "de_outlook": limpar(alert_desc),
                        "de_instrumento": issue_name,
                        "de_isin": de_isin,
                    }
                )

        log.info(
            f"  Página {page}: {len(issue_hits)} emissões, "
            f"{emissoes_com_rating} com ratings (acumulado: {len(rows)} ratings)"
        )
        bar = progress_bar(offset + PAGE_SIZE, total) if total else ""
        print(f"    {bar}")

        offset += PAGE_SIZE
        if offset >= total:
            log.info("Todas as emissões foram processadas.")
            break

        time.sleep(1)

    log.info(f"Total de ratings (emissores + emissões) capturados: {len(rows)}")
    print_done(f"{len(rows)} ratings capturados no total")
    return rows


class FitchRatingsScraper(BaseScraper):
    name = "fitch_ratings"
    group = "ratings"
    enabled = True
    phase = 2
    accumulate = True
    chaves_dedup = ["link", "no_tipo_rating", "de_instrumento"]

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
        print_start("Buscando ratings na API GraphQL da Fitch...")

        todos = []
        try:
            todos = _obter_ratings_via_api()
        except Exception as e:
            log.error(f"Erro ao obter ratings da Fitch: {e}", exc_info=True)
            print_fail(f"Erro ao obter ratings: {e}")

        if not todos:
            log.warning("Nenhum rating obtido da Fitch.")
            print_warn("Nenhum rating obtido")

        df = pd.DataFrame(todos)
        if not df.empty:
            colunas = [c for c in CABECALHO if c in df.columns]
            return df[colunas]
        return df


if __name__ == "__main__":
    FitchRatingsScraper().run()
