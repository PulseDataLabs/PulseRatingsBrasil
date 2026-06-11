"""
Preenche coluna cnpj_emissor no consolidado usando múltiplos buscadores.

Tenta DuckDuckGo primeiro (sem chave), depois Brave Search API (se BRAVE_SEARCH_API_KEY
estiver definida), e por fim Bing Web Search API (se BING_SEARCH_API_KEY estiver definida).
Último recurso após CVM, API e RFB.

Uso:
    python scripts/preencher_cnpj_web.py

Requer: pip install ddgs requests
"""

import csv
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from utils.paths import get_data_dir

from scripts.consolidar_emissores import normalizar
from scripts.preencher_cnpj_api import _matches
from scripts.utils.ux import (
    banner, section, bold, dim, green, red, yellow, cyan,
    print_start, print_done, print_fail, print_warn, print_skip, print_info,
    print_summary, print_table,
)

logger = logging.getLogger("preencher_cnpj_web")

COLUNAS_CONSOLIDADO = [
    "no_emissor_padronizado",
    "no_emissor_fitch",
    "no_emissor_moodys",
    "no_emissor_standard_and_poors",
    "no_emissor_austin",
    "no_emissor_liberum",
    "cnpj_emissor",
]

_RE_CNPJ = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")

_SEARCH_APIS: dict[str, dict] = {
    "brave": {
        "env_key": "BRAVE_SEARCH_API_KEY",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "headers": ["X-Subscription-Token"],
        "results_path": ["web", "results"],
        "title_field": "title",
        "body_field": "description",
        "href_field": "url",
    },
    "bing": {
        "env_key": "BING_SEARCH_API_KEY",
        "url": "https://api.bing.microsoft.com/v7.0/search",
        "headers": ["Ocp-Apim-Subscription-Key"],
        "results_path": ["webPages", "value"],
        "title_field": "name",
        "body_field": "snippet",
        "href_field": "url",
    },
    "searxng": {
        "env_key": None,
        "url": None,
        "headers": [],
        "results_path": ["results"],
        "title_field": "title",
        "body_field": "content",
        "href_field": "url",
    },
}


def _api_search(query: str, api_name: str, max_results: int = 5) -> list[dict]:
    """Consulta uma API de busca configurada em _SEARCH_APIS. Retorna [{title, body, href}, ...]."""
    config = _SEARCH_APIS.get(api_name)
    if not config:
        return []
    if config.get("env_key"):
        api_key = os.environ.get(config["env_key"])
        if not api_key:
            return []
        headers = {k: api_key for k in config["headers"]}
    else:
        headers = {}
    url = config["url"] or os.environ.get("SEARXNG_URL", "http://localhost:8888/search")
    try:
        resp = requests.get(
            url,
            params={"q": query, "count": max_results, "format": "json"},
            headers={**headers, "Accept": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []
    items = data
    for key in config["results_path"]:
        if isinstance(items, dict):
            items = items.get(key, {}) if isinstance(items.get(key), (dict, list)) else {}
        elif isinstance(items, list) and isinstance(key, int):
            items = items[key] if key < len(items) else {}
        else:
            items = {}
    if not isinstance(items, list):
        items = []
    return [
        {
            "title": item.get(config["title_field"], ""),
            "body": item.get(config["body_field"], ""),
            "href": item.get(config["href_field"], ""),
        }
        for item in items
    ]


def _brave(query: str, max_results: int = 5) -> list[dict]:
    return _api_search(query, "brave", max_results)


def _bing(query: str, max_results: int = 5) -> list[dict]:
    return _api_search(query, "bing", max_results)


def _searxng(query: str, max_results: int = 5) -> list[dict]:
    return _api_search(query, "searxng", max_results)


def _buscar(
    query: str,
    max_results: int = 5,
    ddgs=None,
) -> tuple[list[dict], str]:
    """Tenta DuckDuckGo → SearXNG → Brave → Bing. Retorna (resultados, nome_do_buscador)."""
    if ddgs is not None:
        try:
            results = ddgs.text(query, max_results=max_results)
            if results:
                return (results or []), "DuckDuckGo"
        except Exception:
            pass

    for nome_buscador, funcao in [
        ("SearXNG", _searxng),
        ("Brave", _brave),
        ("Bing", _bing),
    ]:
        results = funcao(query, max_results)
        if results:
            return results, nome_buscador

    return [], ""


def _texto_sem_cnpj(texto: str) -> str:
    return _RE_CNPJ.sub(" ", texto)


def _limpar_cnpj(valor: Optional[str]) -> str:
    if not valor:
        return ""
    return re.sub(r"\D", "", valor)


def _obter_nome_busca(row: dict) -> str:
    for col in ["no_emissor_fitch", "no_emissor_moodys", "no_emissor_standard_and_poors", "no_emissor_austin", "no_emissor_liberum"]:
        nome = (row.get(col) or "").strip()
        if nome:
            return nome
    return (row.get("no_emissor_padronizado") or "").strip()


def _salvar_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for r in rows:
        r.pop(None, None)
        r.pop("", None)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CONSOLIDADO)
        writer.writeheader()
        writer.writerows(rows)


def _consultar_cnpj_reverso(cnpj_base: str) -> tuple[str | None, bool | None]:
    """Consulta o nome da empresa a partir do CNPJ em sites externos.

    Returns:
        Tupla (nome, is_matriz):
          - nome: nome da empresa ou None se não encontrado
          - is_matriz: True se matriz, False se filial, None se desconhecido
    """
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        return None, None

    # 1. cnpja.com — SSR via SvelteKit __data.json (contém info matriz/filial)
    try:
        r = cffi_requests.get(
            f"https://cnpja.com/office/{cnpj_base}/__data.json",
            impersonate="chrome",
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            nodes = data.get("nodes", [])
            if len(nodes) >= 3:
                office_node = nodes[2]
                if isinstance(office_node, dict) and office_node.get("type") == "data":
                    d = office_node.get("data", [])
                    if len(d) >= 3:
                        fields = d[1]
                        if isinstance(fields, dict) and isinstance(fields.get("company"), int):
                            company_obj = d[fields["company"]]
                            if isinstance(company_obj, dict) and isinstance(company_obj.get("name"), int):
                                name = d[company_obj["name"]]
                                head_index = fields.get("head")
                                is_matriz = None
                                if isinstance(head_index, int) and head_index < len(d):
                                    is_matriz = bool(d[head_index])
                                if isinstance(name, str) and name.strip():
                                    return name.strip(), is_matriz
    except Exception:
        pass

    # 2. cnpj.biz — fallback, parser do <title> (não distingue matriz/filial)
    try:
        r = cffi_requests.get(
            f"https://cnpj.biz/{cnpj_base}",
            impersonate="chrome",
            timeout=10,
        )
        if r.status_code == 200:
            m = re.search(r"<title>(.*?)</title>", r.text, re.DOTALL)
            if m:
                title = m.group(1)
                nome = re.sub(r"\s*\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\s*$", "", title).strip()
                if nome and "|" not in nome:
                    return nome, None
    except Exception:
        pass

    return None, None


def generate(
    consolidado_path: Optional[Path] = None,
    rate_limit: float = 1.5,
    quiet: bool = False,
) -> dict:
    load_dotenv()

    if consolidado_path is None:
        consolidado_path = get_data_dir() / "emissores_consolidado.csv"

    banner(
        "Preenchimento de CNPJ via Busca Web",
        "DuckDuckGo → Brave → Bing · último recurso",
    )

    if not consolidado_path.exists():
        print_fail(f"Consolidado não encontrado: {consolidado_path}")
        return {"total": 0, "matched": 0, "unmatched": 0, "errors": 0}

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r.pop(None, None)
        r.pop("", None)

    pendentes = [r for r in rows if not (r.get("cnpj_emissor") or "").strip()]
    ja_preenchidos = len(rows) - len(pendentes)

    print_info(
        f"Consolidado: {len(rows)} emissores · {green(str(ja_preenchidos))} já preenchidos · {yellow(str(len(pendentes)))} pendentes"
    )

    if not pendentes:
        print_done("Nenhum emissor pendente — consolidado já completo")
        return {"total": len(rows), "matched": 0, "unmatched": 0, "errors": 0}

    try:
        from ddgs import DDGS
    except ImportError:
        print_fail("ddgs não instalado. Execute: pip install ddgs")
        return {"total": 0, "matched": 0, "unmatched": 0, "errors": 0, "missing_dep": True}

    proxy_url = os.environ.get("CNPJABERTO_PROXY")

    print_start(f"Buscando {len(pendentes)} emissores (DuckDuckGo → Brave → Bing)...")
    print()

    section("Progresso", "search")

    nomes_pendentes = []
    for row in rows:
        if (row.get("cnpj_emissor") or "").strip():
            continue
        n = _obter_nome_busca(row)
        if n:
            nomes_pendentes.append(n)
    max_width = min(max(len(n) for n in nomes_pendentes), 60)

    matched = 0
    unmatched = 0
    errors = 0
    engine_usage: dict[str, int] = {}

    with DDGS(proxy=proxy_url, timeout=15) as ddgs:
        for i, row in enumerate(rows):
            cnpj_existente = (row.get("cnpj_emissor") or "").strip()
            if cnpj_existente:
                continue

            nome_busca = _obter_nome_busca(row)
            if not nome_busca:
                unmatched += 1
                continue

            nome_pad = (row.get("no_emissor_padronizado") or "").strip()
            if not nome_pad:
                unmatched += 1
                continue

            cnpj = None
            query = f'"{nome_busca}" CNPJ'

            try:
                results, engine = _buscar(query, max_results=5, ddgs=ddgs)
            except Exception as e:
                errors += 1
                if not quiet:
                    print(f"  {red('✖')}  {dim(nome_busca):{max_width}s}  {red('erro busca')}  {dim(str(e)[:40])}")
                if i < len(rows) - 1:
                    time.sleep(rate_limit)
                continue

            if not results:
                unmatched += 1
                if not quiet:
                    print(f"  {yellow('⚠')}  {dim(nome_busca):{max_width}s}  {yellow('não encontrado nos buscadores')}")
                if i < len(rows) - 1:
                    time.sleep(rate_limit)
                continue

            engine_usage[engine] = engine_usage.get(engine, 0) + 1

            cnpjs_encontrados: set[str] = set()
            for result in results or []:
                texto = f"{result.get('title', '')} {result.get('body', '')}"
                for match in _RE_CNPJ.finditer(texto):
                    raw = match.group()
                    cnpjs_encontrados.add(_limpar_cnpj(raw))

            if not cnpjs_encontrados:
                unmatched += 1
                if not quiet:
                    print(f"  {yellow('⚠')}  {dim(nome_busca):{max_width}s}  {yellow('sem CNPJ nos resultados')}")
                if i < len(rows) - 1:
                    time.sleep(rate_limit)
                continue

            if len(cnpjs_encontrados) == 1:
                cnpj = list(cnpjs_encontrados)[0]
            else:
                # tenta desambiguar: usa o CNPJ do primeiro resultado cujo
                # title ou body (sem CNPJ) normalize como nome_pad
                for result in results or []:
                    title = result.get("title", "") or ""
                    body = result.get("body", "") or ""
                    if (
                        normalizar(_texto_sem_cnpj(title)) == nome_pad
                        or normalizar(_texto_sem_cnpj(body)) == nome_pad
                    ):
                        texto = f"{title} {body}"
                        for match in _RE_CNPJ.finditer(texto):
                            cnpj = _limpar_cnpj(match.group())
                            break
                    if cnpj:
                        break

                # consulta reversa: confirma cada candidato em sites externos
                if not cnpj:
                    matching: list[tuple[str, bool | None]] = []
                    for candidato in sorted(cnpjs_encontrados):
                        nome_rv, is_matriz = _consultar_cnpj_reverso(candidato)
                        if nome_rv and _matches(nome_rv, nome_pad):
                            matching.append((candidato, is_matriz))
                    # Prioriza CNPJ da matriz sobre filiais
                    for candidato, is_matriz in matching:
                        if is_matriz:
                            cnpj = candidato
                            break
                    if not cnpj and matching:
                        cnpj = matching[0][0]

                if not cnpj:
                    unmatched += 1
                    if not quiet:
                        cnpjs_str = ", ".join(sorted(cnpjs_encontrados))
                        print(f"  {yellow('⚠')}  {dim(nome_busca):{max_width}s}  {yellow(f'{len(cnpjs_encontrados)} CNPJs, ambíguo: {cnpjs_str}')}")
                    if i < len(rows) - 1:
                        time.sleep(rate_limit)
                    continue

            if cnpj:
                row["cnpj_emissor"] = cnpj
                matched += 1
                if not quiet:
                    print(f"  {green('✔')}  {dim(nome_busca):{max_width}s}  {green(cnpj)}")
                _salvar_csv(consolidado_path, rows)
            else:
                unmatched += 1
                if not quiet:
                    print(f"  {yellow('⚠')}  {dim(nome_busca):{max_width}s}  {yellow('não encontrado')}")

            if i < len(rows) - 1:
                time.sleep(rate_limit)

    print()
    section("Resumo", "chart")

    rows_table = [
        (green("✔"), "Preenchidos", str(matched)),
        (yellow("⚠"), "Não encontrados", str(unmatched)),
        (red("✖"), "Erros", str(errors)),
        (cyan("ℹ"), "Total processados", str(matched + unmatched + errors)),
    ]
    if engine_usage:
        for eng, cnt in sorted(engine_usage.items()):
            rows_table.append((dim("ℹ"), f"  via {eng}", str(cnt)))
    print_table(
        [(label, val) for _, label, val in rows_table],
        ["", "Quantidade"],
        title="CNPJs via Busca Web",
    )

    print_summary(
        "Preenchimento via Busca Web",
        total=len(rows),
        success=matched,
        failed=errors,
        skipped=0,
        elapsed=0,
        details=[("file", "CSV", str(consolidado_path))],
    )

    return {
        "total": len(rows),
        "matched": matched,
        "unmatched": unmatched,
        "errors": errors,
    }


def main():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    result = generate()

    if result.get("missing_dep"):
        sys.exit(1)

    print()
    if result["matched"] > 0:
        print(f"  {green('✔')}  {result['matched']} CNPJs preenchidos")
    if result["unmatched"] > 0:
        print(f"  {yellow('⚠')}  {result['unmatched']} não encontrados")
    if result["errors"] > 0:
        print(f"  {red('✖')}  {result['errors']} erro(s)")
    total_encontrados = result["matched"] + result.get("pre_existing", 0)
    print(f"  {dim('─')}")
    print(f"  {bold('Total no consolidado:')} {result['total']} emissores")


if __name__ == "__main__":
    main()
