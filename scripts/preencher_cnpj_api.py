"""
Preenche coluna cnpj_emissor no consolidado usando CNPJ Aberto API.
Requer: pip install cnpjaberto
Requer: CNPJABERTO_API_KEY no .env ou environment (free: 1.000 req/dia)
"""

import csv
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from scripts.consolidar_emissores import normalizar

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


def generate(
    consolidado_path: Optional[Path] = None,
    rate_limit: float = 1.0,
    dry_run: bool = False,
) -> dict:
    if consolidado_path is None:
        consolidado_path = (
            Path(__file__).resolve().parents[1] / "data" / "emissores_consolidado.csv"
        )

    logger.info("=" * 50)
    logger.info("PREENCHE CNPJ (API CNPJ Aberto)")
    logger.info("=" * 50)

    api_key = os.environ.get("CNPJABERTO_API_KEY")
    if not api_key:
        logger.warning("CNPJABERTO_API_KEY não definida. Pulando preenchimento via API.")
        return {"matched": 0, "unmatched": 0, "errors": 0, "total": 0, "skipped_no_key": True}

    if not consolidado_path.exists():
        logger.warning(f"Consolidado não encontrado: {consolidado_path}")
        return {"matched": 0, "unmatched": 0, "errors": 0, "total": 0}

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if dry_run:
        pendentes = [r for r in rows if not (r.get("cnpj_emissor") or "").strip()]
        logger.info(f"Dry-run: {len(pendentes)} emissores pendentes de {len(rows)} total")
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
        logger.error("cnpjaberto não instalado. Execute: pip install cnpjaberto")
        return {"matched": 0, "unmatched": 0, "errors": 0, "total": 0, "missing_dep": True}

    total = len(rows)
    matched = 0
    unmatched = 0
    errors = 0

    updated_rows: list[dict] = []

    with Client() as client:
        for i, row in enumerate(rows):
            cnpj_existente = (row.get("cnpj_emissor") or "").strip()
            if cnpj_existente:
                updated_rows.append(row)
                continue

            nome_busca = _obter_nome_busca(row)
            if not nome_busca:
                updated_rows.append(row)
                unmatched += 1
                continue

            nome_pad = (row.get("nome_emissor_padronizado") or "").strip()
            if not nome_pad:
                updated_rows.append(row)
                unmatched += 1
                continue

            try:
                resp = client.search(nome_busca, per_page=5)
            except Exception as e:
                logger.warning(f"Erro na busca por '{nome_busca}': {e}")
                updated_rows.append(row)
                errors += 1
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
            else:
                unmatched += 1

            updated_rows.append(row)

            if i < len(rows) - 1:
                time.sleep(rate_limit)

    consolidado_path.parent.mkdir(parents=True, exist_ok=True)
    with open(consolidado_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CONSOLIDADO)
        writer.writeheader()
        writer.writerows(updated_rows)

    logger.info(
        f"Total: {total} | Preenchidos: {matched} | "
        f"Não encontrados: {unmatched} | Erros: {errors}"
    )

    return {
        "total": total,
        "matched": matched,
        "unmatched": unmatched,
        "errors": errors,
    }


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    result = generate()
    key_status = " (sem API key)" if result.get("skipped_no_key") else ""
    print(f"Resultado: {result['matched']} CNPJs preenchidos de {result['total']} emissores{key_status}")


if __name__ == "__main__":
    main()
