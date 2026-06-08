"""
Preenche coluna cnpj_emissor no consolidado usando a base pública da RFB.

Uso LOCAL apenas: python scripts/preencher_cnpj_rfb.py

Pipeline:
  1. Verifica se DADOS_ABERTOS_CNPJ.zip existe (instrui download se não)
  2. Extrai EMPRECSV, carrega em SQLite com índice por nome normalizado
  3. Para cada emissor sem CNPJ, busca por nome normalizado + fallback
  4. Salva incrementalmente no consolidado
"""

import argparse
import csv
import logging
import re
import sqlite3
import sys
import zipfile
from pathlib import Path
from typing import Optional

from scripts.consolidar_emissores import normalizar
from scripts.utils.ux import (
    banner,
    bold,
    cyan,
    dim,
    green,
    print_done,
    print_fail,
    print_info,
    print_start,
    print_summary,
    print_table,
    print_warn,
    red,
    section,
    white,
    yellow,
)

logger = logging.getLogger("preencher_cnpj_rfb")

COLUNAS_CONSOLIDADO = [
    "nome_emissor_padronizado",
    "nome_emissor_fitch",
    "nome_emissor_moodys",
    "nome_emissor_standard_and_poors",
    "cnpj_emissor",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONSOLIDADO_PATH = PROJECT_ROOT / "data" / "emissores_consolidado.csv"
CACHE_DIR = PROJECT_ROOT / "data" / "rfb_cache"
ZIP_PATH = CACHE_DIR / "DADOS_ABERTOS_CNPJ.zip"
DB_PATH = CACHE_DIR / "empresas.db"

_PALAVRAS_IGNORAR = {
    "BANCO",
    "SA",
    "S.A",
    "LTDA",
    "EIRELI",
    "MEI",
    "ME",
    "EPP",
    "DO",
    "DA",
    "DOS",
    "DAS",
    "DE",
    "EM",
    "COM",
    "E",
    "OU",
    "A",
    "AO",
    "AOS",
    "AS",
    "O",
    "OS",
    "NO",
    "NA",
    "PELO",
    "PELA",
    "UM",
    "UMA",
    "LIMITED",
    "INC",
    "CORP",
    "LLC",
    "COMERCIAL",
    "INDUSTRIAL",
    "PARTICIPACOES",
    "PART",
    "HOLDING",
    "ADMINISTRACAO",
    "ADMIN",
    "ASSESSORIA",
    "CONSULTORIA",
    "SERVICOS",
    "SERVIÇOS",
    "IMPORTACAO",
    "EXPORTACAO",
    "IMPORTAÇÃO",
    "EXPORTAÇÃO",
    "TRANSPORTES",
    "LOGISTICA",
    "LOGÍSTICA",
    "BRASIL",
    "SAO",
}


def _calcular_dv(cnpj_base_12: str) -> str:
    if len(cnpj_base_12) != 12:
        cnpj_base_12 = cnpj_base_12.zfill(12)[:12]
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj_base_12[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    cnpj_com_dv1 = cnpj_base_12 + str(dv1)
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj_com_dv1[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    return f"{dv1}{dv2}"


def _montar_cnpj(cnpj_base: str, ordem: str = "0001") -> str:
    base_12 = cnpj_base.zfill(8) + ordem
    return base_12 + _calcular_dv(base_12)


def _extrair_palavras(nome: str) -> set[str]:
    palavras = set(nome.split())
    return {p for p in palavras if len(p) >= 3 and p not in _PALAVRAS_IGNORAR}


def _build_db(zip_path: Path, db_path: Path) -> None:
    logger.info(f"Construindo banco SQLite em {db_path}...")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA cache_size = -8000000")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS empresas (
            cnpj_base TEXT PRIMARY KEY,
            razao_social TEXT NOT NULL,
            nome_normalizado TEXT NOT NULL
        )
        """
    )
    conn.commit()

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        empresa_file = next((n for n in names if "EMPRECSV" in n.upper()), None)
        if not empresa_file:
            raise FileNotFoundError("Arquivo EMPRECSV não encontrado no zip")

        print_info("Importando EMPRECSV...")
        empresas_rows = 0
        with z.open(empresa_file) as f:
            for line_bytes in f:
                line = line_bytes.decode("latin-1").rstrip("\n\r")
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) < 2:
                    continue
                cnpj_base = parts[0].strip()
                razao = parts[1].strip()
                if not cnpj_base or not razao:
                    continue
                norm = normalizar(razao)
                if not norm:
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO empresas (cnpj_base, razao_social, nome_normalizado) VALUES (?, ?, ?)",
                    (cnpj_base, razao, norm),
                )
                empresas_rows += 1
                if empresas_rows % 500000 == 0:
                    conn.commit()
                    print(f"  {dim(f'{empresas_rows:,}')} empresas...")
        conn.commit()
        print_done(f"{empresas_rows:,} empresas importadas")

    print_info("Criando índices...")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_empresas_norm ON empresas(nome_normalizado)"
    )
    conn.commit()
    conn.close()
    print_done("Banco SQLite pronto")


def _search(
    nome_normalizado: str,
    db_path: Path,
) -> Optional[str]:
    conn = sqlite3.connect(str(db_path))

    cur = conn.execute(
        "SELECT cnpj_base, razao_social FROM empresas WHERE nome_normalizado = ?",
        (nome_normalizado,),
    )
    results = cur.fetchall()

    if len(results) == 1:
        cnpj = _montar_cnpj(results[0][0])
        conn.close()
        return cnpj

    if len(results) > 1:
        conn.close()
        return None

    palavras = _extrair_palavras(nome_normalizado)
    if len(palavras) >= 2:
        conditions = " AND ".join(
            f"nome_normalizado LIKE '%{w}%'" for w in palavras
        )
        cur = conn.execute(
            f"SELECT cnpj_base FROM empresas WHERE {conditions}"
        )
        results = cur.fetchall()
        if len(results) == 1:
            cnpj = _montar_cnpj(results[0][0])
            conn.close()
            return cnpj

    conn.close()
    return None


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
    zip_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    rebuild_db: bool = False,
    quiet: bool = False,
) -> dict:
    if consolidado_path is None:
        consolidado_path = CONSOLIDADO_PATH
    if zip_path is None:
        zip_path = ZIP_PATH
    if db_path is None:
        db_path = DB_PATH

    banner(
        "Preenchimento de CNPJ via Base RFB",
        "Dados públicos da Receita Federal · Local apenas",
    )

    if not zip_path.exists():
        print_fail(f"Arquivo não encontrado: {zip_path}")
        print()
        print_info("Baixe o DADOS_ABERTOS_CNPJ.zip manualmente de:")
        print(
            f"  {cyan('https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj')}"
        )
        print(f"  {dim('ou')}")
        print(
            f"  {cyan('https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/')}"
        )
        print()
        print_info("Salve em:")
        print(f"  {white(str(zip_path))}")
        print()
        print_warn("Após baixar, execute novamente o script.")
        return {
            "total": 0,
            "matched": 0,
            "unmatched": 0,
            "errors": 0,
            "missing_zip": True,
        }

    if not consolidado_path.exists():
        print_fail(f"Consolidado não encontrado: {consolidado_path}")
        return {"total": 0, "matched": 0, "unmatched": 0, "errors": 0}

    if rebuild_db or not db_path.exists():
        try:
            _build_db(zip_path, db_path)
        except Exception as e:
            print_fail(f"Erro ao construir banco: {e}")
            return {"total": 0, "matched": 0, "unmatched": 0, "errors": 1}

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r.pop(None, None)
        r.pop("", None)

    pendentes = [
        r for r in rows if not (r.get("cnpj_emissor") or "").strip()
    ]
    ja_preenchidos = len(rows) - len(pendentes)

    print_info(
        f"Consolidado: {len(rows)} emissores · {green(str(ja_preenchidos))} já preenchidos · {yellow(str(len(pendentes)))} pendentes"
    )

    if not pendentes:
        print_done("Nenhum emissor pendente — consolidado já completo")
        return {
            "total": len(rows),
            "matched": 0,
            "unmatched": 0,
            "errors": 0,
        }

    print_start(f"Buscando {len(pendentes)} emissores na base RFB...")
    print()

    section("Progresso", "search")

    matched = 0
    unmatched = 0
    errors = 0

    for row in rows:
        cnpj_existente = (row.get("cnpj_emissor") or "").strip()
        if cnpj_existente:
            continue

        nome_pad = (row.get("nome_emissor_padronizado") or "").strip()
        if not nome_pad:
            unmatched += 1
            continue

        try:
            cnpj = _search(nome_pad, db_path)
        except Exception as e:
            if not quiet:
                print(
                    f"  {red('✖')}  {dim(nome_pad)}  {red('erro')}  {dim(str(e)[:40])}"
                )
            errors += 1
            continue

        if cnpj:
            row["cnpj_emissor"] = cnpj
            matched += 1
            if not quiet:
                print(f"  {green('✔')}  {dim(nome_pad)}  {green(cnpj)}")
            _salvar_csv(consolidado_path, rows)
        else:
            unmatched += 1
            if not quiet:
                print(
                    f"  {yellow('⚠')}  {dim(nome_pad)}  {yellow('não encontrado')}"
                )

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
        title="CNPJs via RFB",
    )

    print_summary(
        "Preenchimento via RFB",
        total=len(rows),
        success=matched,
        failed=errors,
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
    parser = argparse.ArgumentParser(
        description="Preenche CNPJs via base RFB"
    )
    parser.add_argument(
        "--rebuild-db",
        action="store_true",
        help="Recria o banco SQLite do zero",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suprime output detalhado",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    result = generate(rebuild_db=args.rebuild_db, quiet=args.quiet)

    print()
    if result.get("missing_zip"):
        print(f"  {red('✖')}  Zip da RFB não encontrado. Baixe manualmente.")
        sys.exit(1)
    elif result["matched"] > 0:
        print(f"  {green('✔')}  {result['matched']} CNPJs preenchidos")
    if result["unmatched"] > 0:
        print(
            f"  {yellow('⚠')}  {result['unmatched']} não encontrados"
        )
    if result["errors"] > 0:
        print(f"  {red('✖')}  {result['errors']} erro(s)")
    print(f"  {dim('─')}")
    print(f"  {bold('Total no consolidado:')} {result['total']} emissores")


if __name__ == "__main__":
    main()
