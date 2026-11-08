import json
import threading
import time
from pathlib import Path

from curl_cffi import requests

from scripts.utils import print_fail

BASE_API_URL = "https://sitev2-api.liberumratings.com.br"
CACHE_FILE = Path("/tmp/liberum_raw_items.json")
CACHE_MAX_AGE_SECONDS = 7200  # 2 horas
_FETCH_LOCK = threading.Lock()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Origin": "https://www.liberumratings.com.br",
    "Referer": "https://www.liberumratings.com.br/",
    "Accept": "application/json, text/plain, */*",
}


def get_liberum_raw_items(logger) -> list[dict]:
    """
    Busca todas as páginas da API da Liberum com lock de thread e cache de 2h em /tmp,
    evitando que liberum_emissores e liberum_ratings paginem 85+ vezes em duplicidade.
    """
    with _FETCH_LOCK:
        if CACHE_FILE.exists():
            try:
                file_age = time.time() - CACHE_FILE.stat().st_mtime
                if file_age < CACHE_MAX_AGE_SECONDS and CACHE_FILE.stat().st_size > 100:
                    with CACHE_FILE.open("r", encoding="utf-8") as f:
                        cached = json.load(f)
                    if isinstance(cached, list) and cached:
                        logger.info(
                            f"Reutilizando cache da API Liberum ({len(cached)} itens, {file_age / 60:.1f} min)."
                        )
                        return cached
            except Exception as e:
                logger.warning(f"Falha ao ler cache da Liberum: {e}")

        all_items: list[dict] = []
        page = 1
        items_per_page = 40
        total_pages = 1
        max_retries = 3

        while page <= total_pages:
            logger.info(f"Buscando página {page}/{total_pages} na API Liberum...")
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
                        timeout=45,
                    )
                    resp.raise_for_status()
                    data_json = resp.json()
                    break
                except Exception as e:
                    logger.warning(f"Tentativa {attempt + 1} falhou para a página {page}: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"Erro persistente na página {page}: {e}")
                        print_fail(f"Erro ao acessar API Liberum na página {page}: {e}")
                        break
                    time.sleep(2**attempt)

            if data_json is None:
                break

            if page == 1:
                total_pages = data_json.get("pages", 1)
                logger.info(f"Total de páginas a buscar: {total_pages}")

            items = data_json.get("data", [])
            if not items:
                logger.info("Página vazia. Fim da paginação.")
                break

            all_items.extend(items)
            page += 1
            time.sleep(0.25)

        if all_items:
            try:
                temp_file = CACHE_FILE.with_suffix(".tmp")
                with temp_file.open("w", encoding="utf-8") as f:
                    json.dump(all_items, f, ensure_ascii=False)
                temp_file.replace(CACHE_FILE)
            except Exception as e:
                logger.warning(f"Não foi possível gravar cache da Liberum: {e}")

        return all_items

