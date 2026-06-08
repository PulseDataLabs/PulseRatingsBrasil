"""
Preenche coluna cnpj_emissor no consolidado usando a base pública da RFB.

Uso LOCAL apenas: python scripts/preencher_cnpj_rfb.py

Pipeline:
  1. Descobre mês mais recente via WebDAV no repositório da RFB
  2. Baixa os Empresas{N}.zip do mês (~1.4GB total, 10 arquivos)
  3. Extrai CNPJ_BASE + RAZAO_SOCIAL, carrega em SQLite com índice
  4. Para cada emissor sem CNPJ, busca por nome normalizado + fallback
  5. Salva incrementalmente no consolidado
"""

import argparse
import csv
import io
import logging
import re
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Optional

import requests

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
DB_PATH = CACHE_DIR / "empresas.db"

RFB_BASE_URL = (
    "https://arquivos.receitafederal.gov.br"
    "/public.php/dav/files/YggdBLfdninEJX9/"
)

NS = {"d": "DAV:", "oc": "http://owncloud.org/ns", "nc": "http://nextcloud.org/ns"}

_PALAVRAS_IGNORAR = {
    "BANCO", "SA", "S.A", "LTDA", "EIRELI", "MEI", "ME", "EPP",
    "DO", "DA", "DOS", "DAS", "DE", "EM", "COM", "E", "OU",
    "A", "AO", "AOS", "AS", "O", "OS", "NO", "NA",
    "PELO", "PELA", "UM", "UMA",
    "LIMITED", "INC", "CORP", "LLC",
    "COMERCIAL", "INDUSTRIAL",
    "PARTICIPACOES", "PART", "HOLDING",
    "ADMINISTRACAO", "ADMIN",
    "ASSESSORIA", "CONSULTORIA",
    "SERVICOS", "SERVICOS",
    "IMPORTACAO", "EXPORTACAO", "IMPORTACAO", "EXPORTACAO",
    "TRANSPORTES", "LOGISTICA", "LOGISTICA",
    "BRASIL", "SAO",
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


# ── WebDAV ──────────────────────────────────────────────────────────────


def _xml_text(parent, tag: str) -> Optional[str]:
    el = parent.find(tag, NS)
    return el.text if el is not None else None


def _list_dir(url: str) -> list[dict]:
    resp = requests.request("PROPFIND", url, headers={"Depth": "1"}, timeout=60)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    entries = []
    base_href = url.rstrip("/") + "/"
    for response in root.findall("d:response", NS):
        href = _xml_text(response, "d:href")
        if not href:
            continue
        if href.rstrip("/") == base_href.rstrip("/"):
            continue
        propstat = response.find("d:propstat", NS)
        if propstat is None:
            continue
        prop = propstat.find("d:prop", NS)
        if prop is None:
            continue
        rtype = prop.find("d:resourcetype", NS)
        is_collection = rtype is not None and rtype.find("d:collection", NS) is not None
        size_text = _xml_text(prop, "d:getcontentlength")
        lastmod = _xml_text(prop, "d:getlastmodified")
        entries.append({
            "href": href,
            "name": href.rstrip("/").split("/")[-1],
            "collection": is_collection,
            "size": int(size_text) if size_text else 0,
            "lastmod": lastmod or "",
        })
    return entries


def _mes_mais_recente() -> Optional[str]:
    entries = _list_dir(RFB_BASE_URL)
    meses = sorted(
        (e["name"] for e in entries if e["collection"] and re.match(r"^\d{4}-\d{2}$", e["name"])),
        reverse=True,
    )
    return meses[0] if meses else None


def _empresa_zips_no_mes(mes: str) -> list[dict]:
    url = RFB_BASE_URL + mes + "/"
    entries = _list_dir(url)
    return [
        e for e in entries
        if not e["collection"] and re.match(r"^Empresas\d+\.zip$", e["name"])
    ]


def _baixar(url: str, path: Path, total_size: int = 0, quiet: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, stream=True, timeout=300)
    resp.raise_for_status()
    downloaded = 0
    last_pct = -1
    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
            if not quiet and total_size:
                downloaded += len(chunk)
                pct = int(100 * downloaded / total_size)
                if pct != last_pct:
                    bar = "█" * (pct // 4) + "░" * (25 - pct // 4)
                    print(f"\r  {cyan(bar)}  {dim(f'{pct:3d}%')}  {dim(f'{downloaded//1024//1024}MB / {total_size//1024//1024}MB')}", end="", flush=True)
                    last_pct = pct
    if not quiet:
        print()


def _baixar_empresas(mes: str, cache_dir: Path, quiet: bool = False) -> list[Path]:
    zips = _empresa_zips_no_mes(mes)
    if not zips:
        raise RuntimeError(f"Nenhum Empresas*.zip encontrado em {mes}")
    dest_dir = cache_dir / f"empresas-{mes}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    baixados: list[Path] = []
    for z in sorted(zips, key=lambda x: x["name"]):
        dest = dest_dir / z["name"]
        if dest.exists() and dest.stat().st_size == z.get("size", 0):
            baixados.append(dest)
            continue
        url = RFB_BASE_URL + mes + "/" + z["name"]
        if not quiet:
            print_info(f"Baixando {z['name']} ({z['size']//1024//1024} MB)...")
        _baixar(url, dest, total_size=z.get("size", 0), quiet=quiet)
        baixados.append(dest)
    return baixados


# ── SQLite ──────────────────────────────────────────────────────────────


def _construir_db(zip_paths: list[Path], db_path: Path, quiet: bool = False) -> None:
    logger.info(f"Construindo banco SQLite em {db_path}...")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA cache_size = -8000000")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            cnpj_base TEXT PRIMARY KEY,
            razao_social TEXT NOT NULL,
            nome_normalizado TEXT NOT NULL
        )
    """)
    conn.commit()

    total_linhas = 0
    for zip_path in zip_paths:
        if not quiet:
            print(f"  {dim('Processando')} {zip_path.name}...")
        with zipfile.ZipFile(zip_path, "r") as z:
            empresa_file = next((n for n in z.namelist() if "EMPRECSV" in n.upper()), None)
            if not empresa_file:
                continue
            linhas = 0
            with z.open(empresa_file) as f:
                for line_bytes in f:
                    line = line_bytes.decode("latin-1").strip()
                    if not line:
                        continue
                    parts = [p.strip().strip('"') for p in line.split(";")]
                    if len(parts) < 2:
                        continue
                    cnpj_base = parts[0]
                    razao = parts[1]
                    if not cnpj_base or not razao:
                        continue
                    norm = normalizar(razao)
                    if not norm:
                        continue
                    conn.execute(
                        "INSERT OR IGNORE INTO empresas (cnpj_base, razao_social, nome_normalizado) VALUES (?, ?, ?)",
                        (cnpj_base, razao, norm),
                    )
                    linhas += 1
                    total_linhas += 1
            conn.commit()
            if not quiet:
                print(f"    {dim(f'{linhas:,}')} empresas de {zip_path.name}")
    conn.commit()

    if not quiet:
        print_info(f"{total_linhas:,} empresas no total — criando índices...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_empresas_norm ON empresas(nome_normalizado)")
    conn.commit()
    conn.close()
    if not quiet:
        print_done("Banco SQLite pronto")


# ── Search ──────────────────────────────────────────────────────────────


def _search(nome_normalizado: str, db_path: Path) -> Optional[str]:
    conn = sqlite3.connect(str(db_path))

    cur = conn.execute(
        "SELECT cnpj_base FROM empresas WHERE nome_normalizado = ?",
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
        conditions = " AND ".join(f"nome_normalizado LIKE '%{w}%'" for w in palavras)
        cur = conn.execute(f"SELECT cnpj_base FROM empresas WHERE {conditions}")
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


# ── Generate ────────────────────────────────────────────────────────────


def generate(
    consolidado_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    rebuild_db: bool = False,
    quiet: bool = False,
) -> dict:
    if consolidado_path is None:
        consolidado_path = CONSOLIDADO_PATH
    if db_path is None:
        db_path = DB_PATH

    banner(
        "Preenchimento de CNPJ via Base RFB",
        "Download automático dos Empresas*.zip · Local apenas",
    )

    if not consolidado_path.exists():
        print_fail(f"Consolidado não encontrado: {consolidado_path}")
        return {"total": 0, "matched": 0, "unmatched": 0, "errors": 0}

    if rebuild_db or not db_path.exists():
        mes = _mes_mais_recente()
        if not mes:
            print_fail("Não foi possível descobrir o mês mais recente no repositório RFB")
            return {"total": 0, "matched": 0, "unmatched": 0, "errors": 1}
        print_info(f"Mês mais recente: {mes}")
        print_start("Baixando Empresas*.zip da RFB...")
        try:
            zips = _baixar_empresas(mes, CACHE_DIR, quiet=quiet)
        except Exception as e:
            print_fail(f"Erro ao baixar: {e}")
            return {"total": 0, "matched": 0, "unmatched": 0, "errors": 1}
        try:
            _construir_db(zips, db_path, quiet=quiet)
        except Exception as e:
            print_fail(f"Erro ao construir banco: {e}")
            return {"total": 0, "matched": 0, "unmatched": 0, "errors": 1}
    else:
        if not quiet:
            print_info(f"Usando banco existente: {db_path}")

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r.pop(None, None)
        r.pop("", None)

    pendentes = [r for r in rows if not (r.get("cnpj_emissor") or "").strip()]
    ja_preenchidos = len(rows) - len(pendentes)

    if not quiet:
        print_info(
            f"Consolidado: {len(rows)} emissores · {green(str(ja_preenchidos))} já preenchidos · {yellow(str(len(pendentes)))} pendentes"
        )

    if not pendentes:
        if not quiet:
            print_done("Nenhum emissor pendente — consolidado já completo")
        return {"total": len(rows), "matched": 0, "unmatched": 0, "errors": 0}

    if not quiet:
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
                print(f"  {red('✖')}  {dim(nome_pad)}  {red('erro')}  {dim(str(e)[:40])}")
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
                print(f"  {yellow('⚠')}  {dim(nome_pad)}  {yellow('não encontrado')}")

    if not quiet:
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
    parser = argparse.ArgumentParser(description="Preenche CNPJs via base RFB")
    parser.add_argument("--rebuild-db", action="store_true", help="Recria o banco SQLite do zero")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suprime output detalhado")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    result = generate(rebuild_db=args.rebuild_db, quiet=args.quiet)

    print()
    if result["matched"] > 0:
        print(f"  {green('✔')}  {result['matched']} CNPJs preenchidos")
    if result["unmatched"] > 0:
        print(f"  {yellow('⚠')}  {result['unmatched']} não encontrados")
    if result["errors"] > 0:
        print(f"  {red('✖')}  {result['errors']} erro(s)")
    print(f"  {dim('─')}")
    print(f"  {bold('Total no consolidado:')} {result['total']} emissores")


if __name__ == "__main__":
    main()
