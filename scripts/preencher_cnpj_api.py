"""
Preenche coluna cnpj_emissor no consolidado usando CNPJ Aberto API.
Requer: pip install cnpjaberto
Requer: CNPJABERTO_API_KEY no .env ou environment (free: 1.000 req/dia)
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
    banner, section, line, bold, dim, green, red, yellow, cyan, white,
    print_start, print_done, print_fail, print_warn, print_skip, print_info,
    print_summary, print_table, progress_bar,
)

load_dotenv()

logger = logging.getLogger("preencher_cnpj_api")

COLUNAS_CONSOLIDADO = [
    "nome_emissor_padronizado",
    "nome_emissor_fitch",
    "nome_emissor_moodys",
    "nome_emissor_standard_and_poors",
    "cnpj_emissor",
    "dt_geracao",
]


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
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CONSOLIDADO)
        writer.writeheader()
        writer.writerows(rows)


def generate(
    consolidado_path: Optional[Path] = None,
    rate_limit: float = 1.0,
    dry_run: bool = False,
    quiet: bool = False,
) -> dict:
    if consolidado_path is None:
        consolidado_path = (
            Path(__file__).resolve().parents[1] / "data" / "emissores_consolidado.csv"
        )

    banner("Preenchimento de CNPJ via API CNPJ Aberto", "1 requisição/segundo · 1.000 req/dia (free)")

    api_key = os.environ.get("CNPJABERTO_API_KEY")
    if not api_key:
        print_warn("CNPJABERTO_API_KEY não definida no .env nem no ambiente")
        print_skip("Preenchimento via API pulado")
        return {"matched": 0, "unmatched": 0, "errors": 0, "total": 0, "skipped_no_key": True}

    if not consolidado_path.exists():
        print_fail(f"Consolidado não encontrado: {consolidado_path}")
        return {"matched": 0, "unmatched": 0, "errors": 0, "total": 0}

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    pendentes = [r for r in rows if not (r.get("cnpj_emissor") or "").strip()]
    ja_preenchidos = len(rows) - len(pendentes)

    print_info(f"Consolidado: {len(rows)} emissores · {green(str(ja_preenchidos))} já preenchidos · {yellow(str(len(pendentes)))} pendentes")

    if not pendentes:
        print_done("Nenhum emissor pendente — consolidado já completo")
        return {"matched": 0, "unmatched": 0, "errors": 0, "total": len(rows)}

    if dry_run:
        print_skip(f"Dry-run: {len(pendentes)} emissores seriam consultados")
        return {
            "matched": 0,
            "unmatched": len(pendentes),
            "errors": 0,
            "total": len(rows),
            "dry_run": True,
            "pendentes": len(pendentes),
        }

    try:
        from cnpjaberto import Client
    except ImportError:
        print_fail("cnpjaberto não instalado. Execute: pip install cnpjaberto")
        return {"matched": 0, "unmatched": 0, "errors": 0, "total": 0, "missing_dep": True}

    print_start(f"Consultando {len(pendentes)} emissores na API CNPJ Aberto...")
    print()

    section("Progresso", "search")

    matched = 0
    unmatched = 0
    errors = 0

    with Client() as client:
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

            try:
                resp = client.search(nome_busca, per_page=5)
            except Exception as e:
                if not quiet:
                    print(f"  {red('✖')}  {dim(nome_busca[:50]):50s}  {red('erro')}  {dim(str(e)[:40])}")
                errors += 1
                if i < len(rows) - 1:
                    time.sleep(rate_limit)
                continue

            hits = (resp or {}).get("results") or []
            cnpj = None

            for hit in hits:
                hit_nome = (hit.get("razao_social") or "").strip()
                hit_cnpj = _limpar_cnpj(hit.get("cnpj") or "")
                if not hit_nome or not hit_cnpj or len(hit_cnpj) != 14:
                    continue
                if normalizar(hit_nome) == nome_pad:
                    cnpj = hit_cnpj
                    break

            if cnpj:
                row["cnpj_emissor"] = cnpj
                matched += 1
                if not quiet:
                    print(f"  {green('✔')}  {dim(nome_busca[:50]):50s}  {green(cnpj)}")
                _salvar_csv(consolidado_path, rows)
            else:
                unmatched += 1
                if not quiet:
                    print(f"  {yellow('⚠')}  {dim(nome_busca[:50]):50s}  {yellow('não encontrado')}")

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
        title="CNPJs via API",
    )

    print_summary(
        "Preenchimento via API",
        total=len(rows),
        success=matched,
        failed=errors,
        skipped=0,
        elapsed=0,
        details=[
            ("file", "CSV", str(consolidado_path)),
        ],
    )

    if errors:
        print_warn(f"{errors} erro(s) durante a consulta — verifique rede e cota diária")
    if unmatched:
        print_info(f"{unmatched} emissor(es) não encontrado(s) — podem precisar de busca manual")

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

    if result.get("skipped_no_key"):
        sys.exit(1)
    elif result.get("missing_dep"):
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
