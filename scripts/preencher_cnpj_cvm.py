"""
Preenche coluna cnpj_emissor no consolidado usando dados offline da CVM:
- cad_cia_aberta.csv (cias abertas) — CNPJ_CIA + DENOM_SOCIAL
- cad_fi.csv (fundos) — CNPJ_ADMIN + ADMIN, CPF_CNPJ_GESTOR + GESTOR
"""

import csv
import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from utils.paths import get_data_dir

from scripts.consolidar_emissores import normalizar

logger = logging.getLogger("preencher_cnpj_cvm")

CVM_CIA_URL = (
    "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
)
CVM_FI_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"

CACHE_DIR = get_data_dir() / "cvm_cache"
CACHE_TTL = timedelta(hours=24)

COLUNAS_CONSOLIDADO = [
    "no_emissor_padronizado",
    "no_emissor_fitch",
    "no_emissor_moodys",
    "no_emissor_standard_and_poors",
    "no_emissor_austin",
    "no_emissor_liberum",
    "cnpj_emissor",
]


def _limpar_cnpj(valor: Optional[str]) -> str:
    if not valor:
        return ""
    return re.sub(r"\D", "", valor)


def _baixar_csv(url: str, cache_path: Path) -> bool:
    logger.info(f"Baixando {url}...")
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(resp.content)
        logger.info(f"Arquivo salvo em {cache_path} ({len(resp.content)} bytes)")
        return True
    except Exception as e:
        logger.warning(f"Falha ao baixar {url}: {e}")
        return False


def _obter_csv(url: str, filename: str, cache_dir: Path = CACHE_DIR) -> Optional[Path]:
    cache_path = cache_dir / filename
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < CACHE_TTL:
            logger.info(f"Usando cache: {cache_path}")
            return cache_path
    if _baixar_csv(url, cache_path):
        return cache_path
    if cache_path.exists():
        logger.warning(f"Usando cache expirado: {cache_path}")
        return cache_path
    return None


def _ler_csv(caminho: Path, delimiter: str = ";") -> list[dict]:
    with open(caminho, "r", encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)


def _carregar_lookup_cias(caminho: Path) -> dict[str, str]:
    rows = _ler_csv(caminho)
    lookup: dict[str, str] = {}
    ambiguos: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        cnpj = _limpar_cnpj(row.get("CNPJ_CIA", ""))
        nome = (row.get("DENOM_SOCIAL") or "").strip()
        if not cnpj or not nome or len(cnpj) != 14:
            continue
        norm = normalizar(nome)
        if not norm:
            continue
        ambiguos[norm].add(cnpj)

    for norm, cnpjs in ambiguos.items():
        if len(cnpjs) == 1:
            lookup[norm] = next(iter(cnpjs))

    if ambiguos:
        mult = {k: v for k, v in ambiguos.items() if len(v) > 1}
        if mult:
            logger.info(f"Cias abertas: {len(mult)} nomes normalizados com múltiplos CNPJs (ignorados)")

    return lookup


def _carregar_lookup_fundos(caminho: Path) -> dict[str, str]:
    rows = _ler_csv(caminho)
    lookup: dict[str, str] = {}
    ambiguos: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        for col_nome, col_cnpj in [("ADMIN", "CNPJ_ADMIN"), ("GESTOR", "CPF_CNPJ_GESTOR")]:
            nome = (row.get(col_nome) or "").strip()
            cnpj = _limpar_cnpj(row.get(col_cnpj) or "")
            if not cnpj or not nome or len(cnpj) != 14:
                continue
            norm = normalizar(nome)
            if not norm:
                continue
            ambiguos[norm].add(cnpj)

    for norm, cnpjs in ambiguos.items():
        if len(cnpjs) == 1:
            lookup[norm] = next(iter(cnpjs))

    if ambiguos:
        mult = {k: v for k, v in ambiguos.items() if len(v) > 1}
        if mult:
            logger.info(f"Fundos: {len(mult)} nomes normalizados com múltiplos CNPJs (ignorados)")

    return lookup


def generate(
    consolidado_path: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
) -> dict:
    if consolidado_path is None:
        consolidado_path = get_data_dir() / "emissores_consolidado.csv"
    if cache_dir is None:
        cache_dir = CACHE_DIR

    logger.info("=" * 50)
    logger.info("PREENCHE CNPJ (CVM)")
    logger.info("=" * 50)

    cia_path = _obter_csv(CVM_CIA_URL, "cad_cia_aberta.csv", cache_dir)
    fi_path = _obter_csv(CVM_FI_URL, "cad_fi.csv", cache_dir)

    lookup_cia: dict[str, str] = {}
    lookup_fi: dict[str, str] = {}

    if cia_path:
        lookup_cia = _carregar_lookup_cias(cia_path)
        logger.info(f"Cias abertas: {len(lookup_cia)} nomes no lookup")
    else:
        logger.warning("cad_cia_aberta.csv não disponível")

    if fi_path:
        lookup_fi = _carregar_lookup_fundos(fi_path)
        logger.info(f"Fundos (admin+gestor): {len(lookup_fi)} nomes no lookup")
    else:
        logger.warning("cad_fi.csv não disponível")

    if not consolidado_path.exists():
        logger.warning(f"Consolidado não encontrado: {consolidado_path}")
        return {"matched": 0, "unmatched": 0, "ambiguous": 0, "total": 0}

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r.pop(None, None)
        r.pop("", None)

    total = len(rows)
    matched = 0
    unmatched = 0
    ambiguous_hits = 0
    updated_rows: list[dict] = []
    ambiguous_list: list[str] = []

    for row in rows:
        if (row.get("cnpj_emissor") or "").strip():
            updated_rows.append(row)
            continue

        nome_pad = (row.get("no_emissor_padronizado") or "").strip()
        if not nome_pad:
            updated_rows.append(row)
            unmatched += 1
            continue

        cnpj = None
        # Priority: cias abertas, then fundos admin/gestor
        if nome_pad in lookup_cia:
            cnpj = lookup_cia[nome_pad]
        elif nome_pad in lookup_fi:
            cnpj = lookup_fi[nome_pad]

        if cnpj:
            row["cnpj_emissor"] = cnpj
            matched += 1
        else:
            unmatched += 1

        updated_rows.append(row)

    consolidado_path.parent.mkdir(parents=True, exist_ok=True)
    with open(consolidado_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CONSOLIDADO)
        writer.writeheader()
        writer.writerows(updated_rows)

    logger.info(f"Total: {total} | Preenchidos: {matched} | Não encontrados: {unmatched} | Ambíguos: {ambiguous_hits}")
    if ambiguous_list:
        logger.info(f"Ambíguos: {', '.join(ambiguous_list[:10])}{'...' if len(ambiguous_list) > 10 else ''}")

    return {
        "total": total,
        "matched": matched,
        "unmatched": unmatched,
        "ambiguous": ambiguous_hits,
    }


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    result = generate()
    print(f"Resultado: {result['matched']} CNPJs preenchidos de {result['total']} emissores")


if __name__ == "__main__":
    main()
