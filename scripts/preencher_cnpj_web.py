"""
Preenche coluna cnpj_emissor no consolidado usando busca no DuckDuckGo.

Raspagem de snippets em busca de CNPJs. Último recurso após CVM, API e RFB.

Uso:
    python scripts/preencher_cnpj_web.py

Requer: pip install ddgs
"""

import csv
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from scripts.consolidar_emissores import normalizar
from scripts.utils.ux import (
    banner, section, bold, dim, green, red, yellow, cyan,
    print_start, print_done, print_fail, print_warn, print_skip, print_info,
    print_summary, print_table,
)

logger = logging.getLogger("preencher_cnpj_web")

COLUNAS_CONSOLIDADO = [
    "nome_emissor_padronizado",
    "nome_emissor_fitch",
    "nome_emissor_moodys",
    "nome_emissor_standard_and_poors",
    "cnpj_emissor",
]

_RE_CNPJ = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")


def _texto_sem_cnpj(texto: str) -> str:
    """Remove CNPJs do texto antes de normalizar para comparação."""
    return _RE_CNPJ.sub(" ", texto)


def _limpar_cnpj(valor: Optional[str]) -> str:
    if not valor:
        return ""
    return re.sub(r"\D", "", valor)


def _obter_nome_busca(row: dict) -> str:
    for col in ["nome_emissor_fitch", "nome_emissor_moodys", "nome_emissor_standard_and_poors"]:
        nome = (row.get(col) or "").strip()
        if nome:
            return nome
    return (row.get("nome_emissor_padronizado") or "").strip()


def _salvar_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for r in rows:
        r.pop(None, None)
        r.pop("", None)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CONSOLIDADO)
        writer.writeheader()
        writer.writerows(rows)


def generate(
    consolidado_path: Optional[Path] = None,
    rate_limit: float = 1.5,
    quiet: bool = False,
) -> dict:
    load_dotenv()

    if consolidado_path is None:
        consolidado_path = (
            Path(__file__).resolve().parents[1] / "data" / "emissores_consolidado.csv"
        )

    banner(
        "Preenchimento de CNPJ via DuckDuckGo",
        "Busca em snippets · último recurso",
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

    print_start(f"Buscando {len(pendentes)} emissores no DuckDuckGo...")
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

    with DDGS(proxy=proxy_url, timeout=15) as ddgs:
        for i, row in enumerate(rows):
            cnpj_existente = (row.get("cnpj_emissor") or "").strip()
            if cnpj_existente:
                continue

            nome_busca = _obter_nome_busca(row)
            if not nome_busca:
                unmatched += 1
                continue

            nome_pad = (row.get("nome_emissor_padronizado") or "").strip()
            if not nome_pad:
                unmatched += 1
                continue

            cnpj = None
            query = f'"{nome_busca}" CNPJ'

            try:
                results = ddgs.text(query, max_results=5)
            except Exception as e:
                if not quiet:
                    print(f"  {red('✖')}  {dim(nome_busca):{max_width}s}  {red('erro busca')}  {dim(str(e)[:40])}")
                errors += 1
                if i < len(rows) - 1:
                    time.sleep(rate_limit)
                continue

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
                if not cnpj:
                    unmatched += 1
                    if not quiet:
                        print(f"  {yellow('⚠')}  {dim(nome_busca):{max_width}s}  {yellow(f'{len(cnpjs_encontrados)} CNPJs, ambíguo')}")
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
    print_table(
        [(label, val) for _, label, val in rows_table],
        ["", "Quantidade"],
        title="CNPJs via DuckDuckGo",
    )

    print_summary(
        "Preenchimento via DuckDuckGo",
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
