"""
Consolida emissores das 3 agências (Fitch, Moody's, S&P) em um CSV único:
uma linha por emissor, com colunas de nome por fonte + CNPJ.
"""

import csv
import logging
import re
import unicodedata
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.paths import get_data_dir

logger = logging.getLogger("consolidar_emissores")

COLUNAS = [
    "no_emissor_padronizado",
    "no_emissor_fitch",
    "no_emissor_moodys",
    "no_emissor_standard_and_poors",
    "no_emissor_austin",
    "no_emissor_liberum",
    "cnpj_emissor",
]

_SUFIXOS = [
    r"\bS\.?\s*A\b\.?",
    r"\bS/A\b",
    r"\bLTDA?\b\.?",
    r"\bEIRELI\b\.?",
    r"\bME\b",
    r"\bLTD\b\.?",
    r"\bLIMITED\b",
    r"\bINC\b\.?",
    r"\bLLC\b",
    r"\bCORP\b\.?",
]

_PALAVRAS_GENERICAS = [
    r"\bDO\b", r"\bDA\b", r"\bDOS\b", r"\bDAS\b",
    r"\bDE\b", r"\bEM\b", r"\bCOM\b", r"\bE\b", r"\bOU\b",
    r"\bA\b", r"\bAO\b", r"\bAOS\b", r"\bAS\b",
    r"\bO\b", r"\bOS\b", r"\bNO\b", r"\bNA\b",
    r"\bPELO\b", r"\bPELA\b", r"\bUM\b", r"\bUMA\b",
    r"\bBRASIL\b",
]


def normalizar(nome: str) -> str:
    if not nome or not nome.strip():
        return ""

    result = nome.upper().strip()
    result = result.replace("\u2013", "-").replace("\u2014", "-")
    result = result.replace("&", " ")

    result = unicodedata.normalize("NFKD", result)
    result = result.encode("ascii", "ignore").decode("ascii")

    result = re.sub(r"\([^)]*\)", "", result)

    for pattern in _SUFIXOS:
        result = re.sub(pattern, "", result)

    result = re.split(r"\s*[,–\-—;]\s*", result)[0]

    for pattern in _PALAVRAS_GENERICAS:
        result = re.sub(pattern, "", result)

    result = re.sub(r"\s+", " ", result).strip()

    return result


def carregar_emissores_fonte(caminho: Path) -> dict[str, str]:
    if not caminho.exists():
        logger.warning(f"Arquivo não encontrado: {caminho}")
        return {}

    result: dict[str, str] = {}
    with open(caminho, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nome = (row.get("no_emissor") or "").strip()
            if nome:
                result[nome] = normalizar(nome)
    return result


def carregar_consolidado_existente(caminho: Path) -> dict[str, dict]:
    if not caminho.exists():
        return {}

    result: dict[str, dict] = {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row.get("no_emissor_padronizado") or "").strip()
                if key:
                    result[key] = dict(row)
    except Exception as e:
        logger.warning(f"Erro ao ler consolidado existente: {e}")

    return result


def consolidar(
    fitch_path: Path,
    moodys_path: Path,
    sp_path: Path,
    austin_path: Path,
    liberum_path: Path,
    output_path: Path,
) -> None:
    sources = {
        "fitch": carregar_emissores_fonte(fitch_path),
        "moodys": carregar_emissores_fonte(moodys_path),
        "standard_and_poors": carregar_emissores_fonte(sp_path),
        "austin": carregar_emissores_fonte(austin_path),
        "liberum": carregar_emissores_fonte(liberum_path),
    }

    source_padronizados: dict[str, dict[str, str]] = {}
    for source_key, emissor_dict in sources.items():
        pad_map: dict[str, str] = {}
        for original, padronizado in emissor_dict.items():
            if padronizado:
                if padronizado not in pad_map:
                    pad_map[padronizado] = original
        source_padronizados[source_key] = pad_map

    all_padronizados: set[str] = set()
    for pad_map in source_padronizados.values():
        all_padronizados.update(pad_map.keys())

    existing = carregar_consolidado_existente(output_path)

    source_cols = [
        ("fitch", "no_emissor_fitch"),
        ("moodys", "no_emissor_moodys"),
        ("standard_and_poors", "no_emissor_standard_and_poors"),
        ("austin", "no_emissor_austin"),
        ("liberum", "no_emissor_liberum"),
    ]

    rows: list[dict[str, str]] = []
    for padronizado in sorted(all_padronizados):
        row: dict[str, str] = {col: "" for col in COLUNAS}
        row["no_emissor_padronizado"] = padronizado

        for source_key, col_name in source_cols:
            if padronizado in source_padronizados[source_key]:
                row[col_name] = source_padronizados[source_key][padronizado]

        if padronizado in existing:
            cnpj = (existing[padronizado].get("cnpj_emissor") or "").strip()
            if cnpj:
                row["cnpj_emissor"] = cnpj

        rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(
        f"Consolidado gerado: {len(rows)} emissores em {output_path}"
    )


def generate() -> None:
    data_dir = get_data_dir()
    consolidar(
        fitch_path=data_dir / "fitch_emissores.csv",
        moodys_path=data_dir / "moodys_emissores.csv",
        sp_path=data_dir / "standard_and_poors_emissores.csv",
        austin_path=data_dir / "austin_emissores.csv",
        liberum_path=data_dir / "liberum_emissores.csv",
        output_path=data_dir / "emissores_consolidado.csv",
    )


if __name__ == "__main__":
    generate()
