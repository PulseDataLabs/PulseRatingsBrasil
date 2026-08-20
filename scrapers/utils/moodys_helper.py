import datetime
import random
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as crequests

BASE_URL = "https://moodyslocal.com.br"
CACHE_FILE = Path("/tmp/moodys_local_brazil.xlsx")
CACHE_MAX_AGE_SECONDS = 7200  # 2 horas

PROXY_LIST_URLs = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/clkettenbach/free-proxy-sources/main/txt/proxies.txt",
]

IMPERSONATE_PROFILES = ["chrome124", "safari17_0", "chrome", "safari18_0"]


def excel_date_to_str(val) -> str:
    """Converte datas seriais do Excel para string no formato YYYY-MM-DD."""
    if not val:
        return ""
    try:
        fval = float(val)
        d = datetime.date(1899, 12, 30) + datetime.timedelta(days=int(fval))
        return d.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return str(val).split()[0]


def fetch_proxy_list(logger) -> list[str]:
    """Busca uma lista de proxies HTTP gratuitos de repositórios públicos."""
    for url in PROXY_LIST_URLs:
        try:
            logger.info(f"Buscando lista de proxies de {url}...")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                proxies = [p.strip() for p in resp.text.strip().split("\n") if p.strip()]
                if proxies:
                    logger.info(f"Obtidos {len(proxies)} proxies com sucesso.")
                    return proxies
        except Exception as e:
            logger.warning(f"Falha ao buscar proxies de {url}: {e}")
    return []


def get_moodys_session(logger, base_url: str = BASE_URL):
    """
    Tenta abrir conexão direta com a Moody's Local utilizando perfis modernos de impersonate.
    Caso retorne 403 (bloqueio Cloudflare), busca e rotaciona proxies públicos.

    Retorna uma tupla (session, impersonate_profile)
    """
    logger.info("Tentando conexão direta com a Moody's Local...")

    for profile in IMPERSONATE_PROFILES:
        try:
            session = crequests.Session()
            resp = session.get(base_url, impersonate=profile, timeout=20)
            if resp.status_code == 200:
                logger.info(
                    f"Conexão direta bem-sucedida usando perfil {profile}! Nenhum proxy será utilizado."
                )
                return session, profile
            elif resp.status_code == 403:
                logger.warning(f"Perfil {profile} retornou 403 Forbidden.")
            else:
                logger.warning(f"Perfil {profile} retornou status {resp.status_code}.")
        except Exception as e:
            logger.warning(f"Falha no perfil {profile}: {e}")

    logger.warning("Conexões diretas bloqueadas ou falharam. Ativando fallback de proxy...")
    proxies = fetch_proxy_list(logger)
    if not proxies:
        raise RuntimeError("Não foi possível obter nenhuma lista de proxies para fallback.")

    random.shuffle(proxies)
    max_tentativas = min(50, len(proxies))
    logger.info(f"Iniciando testes com até {max_tentativas} proxies aleatórios...")

    for idx, p in enumerate(proxies[:max_tentativas], 1):
        proxy_url = f"http://{p}"
        proxies_dict = {"http": proxy_url, "https": proxy_url}

        logger.info(f"[{idx}/{max_tentativas}] Testando proxy: {proxy_url}")
        test_session = crequests.Session()
        test_session.proxies = proxies_dict

        for profile in ("chrome124", "safari17_0", "chrome"):
            try:
                resp = test_session.get(base_url, impersonate=profile, timeout=10)
                if resp.status_code == 200 and (
                    "moodys" in resp.text.lower()
                    or "classificações" in resp.text.lower()
                    or "vigentes" in resp.text.lower()
                ):
                    logger.info(f"Proxy funcional encontrado! Usando {proxy_url} ({profile})")
                    return test_session, profile
            except Exception:
                pass

    raise RuntimeError("Todos os proxies testados falharam ou foram bloqueados pela Moody's Local.")


def find_download_url(logger, session, profile: str) -> str:
    """Busca o link de download do Excel na página inicial da Moody's Local."""
    resp = session.get(BASE_URL, impersonate=profile, timeout=45)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    download_url = None

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if "Lista de Classificações Vigentes" in text or re.search(
            r"MOODYS_LOCAL_BRAZIL.*\.xlsx?", href, re.IGNORECASE
        ):
            download_url = href if href.startswith("http") else BASE_URL.rstrip("/") + "/" + href.lstrip("/")
            break

    if not download_url:
        raise ValueError("Link do arquivo Excel não encontrado na página da Moody's.")

    return download_url


def ensure_moodys_file_downloaded(logger) -> Path:
    """
    Garante o download do arquivo Excel da Moody's Local.
    Reutiliza cache se o arquivo já existir com tamanho válido (> 1MB) e idade < 2h,
    evitando que scrapers executados em sequência façam downloads duplicados de 60MB.
    """
    if CACHE_FILE.exists():
        file_age = time.time() - CACHE_FILE.stat().st_mtime
        file_size = CACHE_FILE.stat().st_size
        if file_size > 1024 * 1024 and file_age < CACHE_MAX_AGE_SECONDS:
            logger.info(
                f"Reutilizando arquivo Excel em cache: {CACHE_FILE} ({file_size / 1024 / 1024:.2f} MB, {file_age / 60:.1f} min)"
            )
            return CACHE_FILE

    session, profile = get_moodys_session(logger, BASE_URL)
    download_url = find_download_url(logger, session, profile)
    logger.info(f"Link do Excel identificado: {download_url}")

    temp_cache = CACHE_FILE.with_suffix(".tmp")

    for attempt in range(1, 4):
        try:
            logger.info(f"Baixando arquivo Excel (tentativa {attempt}/3, timeout=300s)...")
            resp_file = session.get(download_url, impersonate=profile, timeout=300)
            resp_file.raise_for_status()

            content = resp_file.content
            if len(content) < 1024 * 1024:
                raise ValueError(
                    f"Arquivo baixado muito pequeno ({len(content)} bytes). Possível erro na resposta."
                )

            with temp_cache.open("wb") as f:
                f.write(content)

            temp_cache.replace(CACHE_FILE)
            logger.info(
                f"Download concluído com sucesso: {len(content) / 1024 / 1024:.2f} MB salvos em {CACHE_FILE}"
            )
            return CACHE_FILE
        except Exception as e:
            logger.warning(f"Tentativa {attempt} de download falhou: {e}")
            if attempt == 3:
                raise
            time.sleep(3)

    return CACHE_FILE


def parse_moodys_xlsx(xlsx_path: Path):
    """
    Faz o parse ultra-rápido via streaming XML do XLSX da Moody's Local.
    Evita o carregamento pesado de milhões de células vazias geradas pelo Excel original.

    Retorna (headers, data_rows, file_date)
    """
    zf = zipfile.ZipFile(xlsx_path)
    shared_strings = []

    if "xl/sharedStrings.xml" in zf.namelist():
        with zf.open("xl/sharedStrings.xml") as f:
            for _event, elem in ET.iterparse(f):
                if elem.tag.endswith("}t"):
                    shared_strings.append(elem.text or "")
                elem.clear()

    headers = None
    data_rows = []
    file_date = None

    with zf.open("xl/worksheets/sheet1.xml") as f:
        for _event, elem in ET.iterparse(f, events=("end",)):
            if elem.tag.endswith("}row"):
                cell_dict = {}
                for cell in elem:
                    if cell.tag.endswith("}c"):
                        ref = cell.attrib.get("r", "")
                        col = "".join(c for c in ref if c.isalpha())
                        if col in ("A", "B", "C", "D", "E", "F", "G", "H"):
                            t_type = cell.attrib.get("t")
                            v_elem = cell.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                            if v_elem is not None and v_elem.text is not None:
                                val = v_elem.text
                                if t_type == "s":
                                    idx = int(val)
                                    val = shared_strings[idx] if idx < len(shared_strings) else val
                                cell_dict[col] = val

                # Busca Data de Atualização nos metadados
                if (
                    file_date is None
                    and "G" in cell_dict
                    and "Data de Atualização" in str(cell_dict.get("G", ""))
                ):
                    raw_dt = cell_dict.get("H")
                    if raw_dt:
                        file_date = excel_date_to_str(raw_dt)

                # Busca linha do cabeçalho
                if headers is None:
                    if cell_dict.get("B") == "Emissor" and cell_dict.get("F") == "Rating / Avaliação":
                        headers = [
                            cell_dict.get("A", "Setor"),
                            cell_dict.get("B", "Emissor"),
                            cell_dict.get("C", "Produto"),
                            cell_dict.get("D", "Instrumento"),
                            cell_dict.get("E", "Objeto"),
                            cell_dict.get("F", "Rating / Avaliação"),
                            cell_dict.get("G", "Perspectiva"),
                            cell_dict.get("H", "Última data de atualização"),
                        ]
                else:
                    emissor_val = cell_dict.get("B")
                    if not emissor_val or str(emissor_val).strip() in ("", "None", "-"):
                        elem.clear()
                        break

                    dt_val = excel_date_to_str(cell_dict.get("H", ""))
                    row = [
                        cell_dict.get("A"),
                        cell_dict.get("B"),
                        cell_dict.get("C"),
                        cell_dict.get("D"),
                        cell_dict.get("E"),
                        cell_dict.get("F"),
                        cell_dict.get("G"),
                        dt_val,
                    ]
                    data_rows.append(row)

                elem.clear()

    return headers, data_rows, file_date


def get_moodys_raw_data(logger):
    """
    Função principal unificada:
    1. Baixa/recupera o arquivo Excel com cache e retry.
    2. Realiza o parse eficiente dos dados.

    Retorna (headers, data_rows, file_date)
    """
    xlsx_path = ensure_moodys_file_downloaded(logger)
    return parse_moodys_xlsx(xlsx_path)
