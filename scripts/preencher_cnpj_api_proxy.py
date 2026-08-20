"""
Preenche CNPJs via API CNPJ Aberto com descoberta automática de proxy.

Raspa proxies gratuitos, valida o primeiro funcionando, e delega
o preenchimento ao preencher_cnpj_api.generate() com CNPJABERTO_PROXY
setada no ambiente.

Uso:
    python scripts/preencher_cnpj_api_proxy.py
"""

import os
import re
import sys

import requests
from bs4 import BeautifulSoup

from scripts.preencher_cnpj_api import generate
from scripts.utils.ux import (
    banner,
    bold,
    cyan,
    dim,
    green,
    print_fail,
    print_info,
    print_skip,
    print_start,
    print_warn,
    red,
    section,
    yellow,
)

FONTES = [
    {
        "url": "https://www.free-proxy-list.net/",
        "parser": "html",
    },
    {
        "url": "https://spys.me/proxy.txt",
        "parser": "spys",
    },
    {
        "url": "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all",
        "parser": "text",
    },
    {
        "url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "parser": "text",
    },
]

TIMEOUT_PROXY_LISTA = 10
TIMEOUT_VALIDACAO = 3
MAX_PROXIES_TESTAR = 15


def _raspar_html(url: str) -> list[str]:
    proxies: list[str] = []
    try:
        resp = requests.get(url, timeout=TIMEOUT_PROXY_LISTA)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", id="proxylisttable") or soup.find("table", class_="table")
        if not table:
            tbody = soup.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
            else:
                rows = []
        else:
            rows = table.find_all("tr")
        for tr in rows:
            cols = tr.find_all("td")
            if len(cols) >= 2:
                ip = cols[0].get_text(strip=True)
                porta = cols[1].get_text(strip=True)
                if ip and porta:
                    proxies.append(f"http://{ip}:{porta}")
    except Exception:
        pass
    return proxies


def _raspar_spys(url: str) -> list[str]:
    proxies: list[str] = []
    try:
        resp = requests.get(url, timeout=TIMEOUT_PROXY_LISTA)
        resp.raise_for_status()
        for line in resp.text.splitlines():
            line = line.strip()
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+", line):
                partes = line.split()
                proxy = partes[0].strip()
                proxies.append(f"http://{proxy}")
    except Exception:
        pass
    return proxies


def _raspar_texto(url: str) -> list[str]:
    proxies: list[str] = []
    try:
        resp = requests.get(url, timeout=TIMEOUT_PROXY_LISTA)
        resp.raise_for_status()
        for line in resp.text.splitlines():
            line = line.strip()
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+", line):
                proxies.append(f"http://{line}")
    except Exception:
        pass
    return proxies


def _coletar_proxies() -> list[str]:
    vistos: set[str] = set()
    todas: list[str] = []
    for fonte in FONTES:
        parser = fonte["parser"]
        url = fonte["url"]
        if parser == "html":
            encontradas = _raspar_html(url)
        elif parser == "spys":
            encontradas = _raspar_spys(url)
        else:
            encontradas = _raspar_texto(url)
        for p in encontradas:
            if p not in vistos:
                vistos.add(p)
                todas.append(p)
    return todas


def _validar_proxy(proxy_url: str) -> str | None:
    try:
        resp = requests.get(
            "http://httpbin.org/ip",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=TIMEOUT_VALIDACAO,
        )
        resp.raise_for_status()
        ip = resp.json().get("origin", "")
        if ip and not ip.startswith(proxy_url.split("://")[1].split(":")[0]):
            return ip
    except Exception:
        pass
    return None


def main():
    banner(
        "Proxy Automático para CNPJ Aberto",
        "Raspagem de proxies gratuitos + validação",
    )

    print_start("Coletando proxies de fontes públicas...")
    todas = _coletar_proxies()
    if not todas:
        print_fail("Nenhum proxy encontrado nas fontes")
        print_skip("Executando sem proxy...")
        return generate()

    print_info(f"{len(todas)} proxies únicos coletados")
    print()

    section("Validação", "search")
    proxy_funcional: str | None = None
    ip_externo: str | None = None
    testadas = 0

    for i, proxy in enumerate(todas):
        if i >= MAX_PROXIES_TESTAR:
            break
        testadas += 1
        ip = _validar_proxy(proxy)
        if ip:
            proxy_funcional = proxy
            ip_externo = ip
            print(f"  {green('✔')}  {dim(proxy)}  {cyan(f'→ {ip}')}")
            break
        else:
            print(f"  {dim('·')}  {dim(proxy)}  {dim('falhou')}")

    print()

    if not proxy_funcional:
        print_warn(f"Nenhum proxy funcional encontrado em {testadas} tentativas")
        print_skip("Executando sem proxy...")
        return generate()

    os.environ["HTTP_PROXY"] = proxy_funcional
    os.environ["HTTPS_PROXY"] = proxy_funcional
    os.environ["CNPJABERTO_PROXY"] = proxy_funcional
    print_info(f"Usando proxy: {proxy_funcional} ({cyan(ip_externo or '?')})")
    print()

    return generate()


if __name__ == "__main__":
    result = main()

    print()
    if result.get("skipped_no_key"):
        print(f"  {red('✖')}  CNPJABERTO_API_KEY não definida")
        sys.exit(1)
    elif result.get("missing_dep"):
        print(f"  {red('✖')}  cnpjaberto não instalado")
        sys.exit(1)

    print("  " + dim("─"))
    if result["matched"] > 0:
        print(f"  {green('✔')}  {result['matched']} CNPJs preenchidos")
    if result["unmatched"] > 0:
        print(f"  {yellow('⚠')}  {result['unmatched']} não encontrados")
    if result["errors"] > 0:
        print(f"  {red('✖')}  {result['errors']} erro(s)")
    print(f"  {bold('Total no consolidado:')} {result['total']} emissores")
