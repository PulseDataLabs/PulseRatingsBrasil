import random
import logging
from curl_cffi import requests as crequests
import requests

PROXY_LIST_URLs = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/clkettenbach/free-proxy-sources/main/txt/proxies.txt"
]

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

def get_moodys_session(logger, base_url: str):
    """
    Tenta abrir conexão direta com a Moody's Local.
    Caso retorne 403 (bloqueio do Cloudflare), busca e rotaciona proxies
    públicos até encontrar um funcional.
    
    Retorna uma tupla (session, proxies_dict)
    """
    session = crequests.Session()
    
    logger.info("Tentando conexão direta com a Moody's Local...")
    try:
        resp = session.get(base_url, impersonate="chrome", timeout=15)
        if resp.status_code == 200:
            logger.info("Conexão direta bem-sucedida! Nenhum proxy será utilizado.")
            return session, None
        elif resp.status_code == 403:
            logger.warning("Conexão direta retornou 403 Forbidden. Ativando fallback de proxy...")
        else:
            logger.warning(f"Conexão direta retornou status inesperado {resp.status_code}. Ativando fallback...")
    except Exception as e:
        logger.warning(f"Erro na conexão direta ({e}). Ativando fallback de proxy...")
    
    # Fallback de Proxy
    proxies = fetch_proxy_list(logger)
    if not proxies:
        raise RuntimeError("Não foi possível obter nenhuma lista de proxies para fallback.")
        
    random.shuffle(proxies)
    
    max_tentativas = min(50, len(proxies))
    logger.info(f"Iniciando testes com até {max_tentativas} proxies aleatórios...")
    
    for idx, p in enumerate(proxies[:max_tentativas], 1):
        proxy_url = f"http://{p}"
        proxies_dict = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        logger.info(f"[{idx}/{max_tentativas}] Testando proxy: {proxy_url}")
        test_session = crequests.Session()
        test_session.proxies = proxies_dict
        
        try:
            resp = test_session.get(base_url, impersonate="chrome", timeout=8)
            # Confirma se respondeu 200 e se o conteúdo realmente é da Moody's (evita proxies que retornam páginas de erro ou interceptações)
            if resp.status_code == 200 and ("moodys" in resp.text.lower() or "classificações" in resp.text.lower() or "vigentes" in resp.text.lower()):
                logger.info(f"Proxy funcional encontrado! Usando {proxy_url}")
                return test_session, proxies_dict
            else:
                logger.debug(f"Proxy {proxy_url} retornou status {resp.status_code}")
        except Exception as e:
            logger.debug(f"Falha no proxy {proxy_url}: {e}")
            
    raise RuntimeError("Todos os proxies testados falharam ou foram bloqueados pela Moody's Local.")
