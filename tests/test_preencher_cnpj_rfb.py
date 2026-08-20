import csv
import sqlite3
import zipfile
from pathlib import Path

import pytest

from scripts.preencher_cnpj_rfb import (
    _calcular_dv,
    _montar_cnpj,
    _extrair_palavras,
    _construir_db,
    _search,
    generate,
    COLUNAS_CONSOLIDADO,
)


# ── _calcular_dv ────────────────────────────────────────────────────────


def test_calcular_dv_conhecido():
    """CNPJ 00.000.000/0001-91 → dv = 91"""
    assert _calcular_dv("000000000001") == "91"


def test_calcular_dv_outro():
    assert _calcular_dv("112223330001") == "81"


def test_calcular_dv_padding():
    assert len(_calcular_dv("1")) == 2


# ── _montar_cnpj ────────────────────────────────────────────────────────


def test_montar_cnpj():
    assert _montar_cnpj("00000000") == "00000000000191"


def test_montar_cnpj_base_curta():
    assert _montar_cnpj("1") == "00000001000136"


# ── _extrair_palavras ───────────────────────────────────────────────────


def test_extrair_palavras_filtra_stopwords():
    palavras = _extrair_palavras("BANCO DO BRASIL SA")
    assert "BANCO" not in palavras
    assert "BRASIL" not in palavras
    assert "DO" not in palavras
    assert "SA" not in palavras
    assert palavras == set()


def test_extrair_palavras_curtas_ignoradas():
    palavras = _extrair_palavras("ABC LTDA")
    assert "ABC" in palavras
    assert "LTDA" not in palavras  # stop word


def test_extrair_palavras_mantem_significativas():
    palavras = _extrair_palavras("PETROLEO BRASILEIRO SA")
    assert "PETROLEO" in palavras
    assert "BRASILEIRO" in palavras
    assert "SA" not in palavras


# ── _construir_db ───────────────────────────────────────────────────────


def _criar_zip_emprcsv(zip_path: Path, lines: list[str]):
    """Cria um zip com EMPRECSV content (formato RFB: ; delimitador)."""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines)
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("K3241.K03200Y0.D40000.EMPRECSV", content.encode("latin-1"))


def test_construir_db_basico(tmp_path):
    zip_path = tmp_path / "test.zip"
    db_path = tmp_path / "test.db"

    _criar_zip_emprcsv(zip_path, [
        '00000000;"Ambev S.A.";;',
        '11111111;"Vale S.A.";;',
    ])

    _construir_db([zip_path], db_path)
    assert db_path.exists()

    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("SELECT cnpj_base, nome_normalizado FROM empresas ORDER BY cnpj_base").fetchall()
    conn.close()

    assert len(rows) == 2
    bases = {r[0] for r in rows}
    assert "00000000" in bases
    assert "11111111" in bases


def test_construir_db_zip_sem_emprcsv(tmp_path):
    zip_path = tmp_path / "vazio.zip"
    db_path = tmp_path / "test.db"
    with zipfile.ZipFile(zip_path, "w"):
        pass

    # _construir_db apenas ignora zips sem EMPRECSV, sem erro
    _construir_db([zip_path], db_path)
    assert db_path.exists()
    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]
    conn.close()
    assert count == 0


# ── _search ─────────────────────────────────────────────────────────────


def _criar_db_com_empresas(db_path: Path, empresas: list[tuple[str, str]]):
    """Cria SQLite com empresas: (cnpj_base, razao_social)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS empresas (cnpj_base TEXT PRIMARY KEY, razao_social TEXT NOT NULL, nome_normalizado TEXT NOT NULL)"
    )
    from scripts.consolidar_emissores import normalizar

    for cnpj_base, razao in empresas:
        conn.execute(
            "INSERT OR IGNORE INTO empresas (cnpj_base, razao_social, nome_normalizado) VALUES (?, ?, ?)",
            (cnpj_base, razao, normalizar(razao)),
        )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_empresas_norm ON empresas(nome_normalizado)")
    conn.commit()
    conn.close()


def test_search_exact_match(tmp_path):
    db_path = tmp_path / "test.db"
    _criar_db_com_empresas(db_path, [
        ("00000000", "Ambev S.A."),
    ])

    from scripts.consolidar_emissores import normalizar
    cnpj = _search(normalizar("Ambev S.A."), db_path)
    assert cnpj == "00000000000191"


def test_search_ambiguous(tmp_path):
    db_path = tmp_path / "test.db"
    _criar_db_com_empresas(db_path, [
        ("00000000", "ABC Brasil S.A."),
        ("11111111", "ABC Brasil Ltda."),
    ])

    from scripts.consolidar_emissores import normalizar
    cnpj = _search(normalizar("ABC Brasil S.A."), db_path)
    assert cnpj is None  # ambiguous


def test_search_not_found(tmp_path):
    db_path = tmp_path / "test.db"
    _criar_db_com_empresas(db_path, [
        ("00000000", "Ambev S.A."),
    ])

    from scripts.consolidar_emissores import normalizar
    cnpj = _search(normalizar("Empresa Inexistente Ltda."), db_path)
    assert cnpj is None


def test_search_fallback_palavras(tmp_path):
    """Fallback por palavras encontra empresa quando normalizador dá nomes diferentes."""
    db_path = tmp_path / "test.db"
    _criar_db_com_empresas(db_path, [
        ("00000000", "Companhia de Bebidas São Paulo"),
    ])

    from scripts.consolidar_emissores import normalizar
    cnpj = _search(normalizar("Bebidas São Paulo Ltda."), db_path)
    assert cnpj == "00000000000191"


def test_search_fallback_evita_falso_positivo(tmp_path):
    """Fallback com 2+ resultados retorna None."""
    db_path = tmp_path / "test.db"
    _criar_db_com_empresas(db_path, [
        ("00000000", "Transportes ABC Ltda."),
        ("11111111", "Transportes ABC Cargo Ltda."),
    ])

    from scripts.consolidar_emissores import normalizar
    cnpj = _search(normalizar("ABC Transportes Ltda."), db_path)
    assert cnpj is None


# ── generate ────────────────────────────────────────────────────────────


def _escrever_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CONSOLIDADO)
        writer.writeheader()
        writer.writerows(rows)


def test_generate_preenche(tmp_path):
    db_path = tmp_path / "empresas.db"
    zip_path = tmp_path / "empresas0.zip"
    _criar_zip_emprcsv(zip_path, [
        '00000000;"Ambev S.A.";;',
    ])
    _construir_db([zip_path], db_path)

    consolidado_path = tmp_path / "emissores_consolidado.csv"
    _escrever_csv(consolidado_path, [
        {
            "no_emissor_padronizado": "AMBEV",
            "no_emissor_fitch": "Ambev S.A.",
            "no_emissor_moodys": "",
            "no_emissor_standard_and_poors": "",
            "cnpj_emissor": "",
        },
        {
            "no_emissor_padronizado": "VALE",
            "no_emissor_fitch": "Vale S.A.",
            "no_emissor_moodys": "",
            "no_emissor_standard_and_poors": "",
            "cnpj_emissor": "",
        },
    ])

    result = generate(
        consolidado_path=consolidado_path,
        db_path=db_path,
        rebuild_db=False,
        quiet=True,
    )

    assert result["matched"] == 1
    assert result["unmatched"] == 1

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    cnpjs = {r["no_emissor_padronizado"]: r["cnpj_emissor"] for r in rows}
    assert cnpjs["AMBEV"] == "00000000000191"
    assert cnpjs["VALE"] == ""


def test_generate_consolidado_inexistente(tmp_path):
    """Consolidado não encontrado → erro sem crash."""
    db_path = tmp_path / "empresas.db"
    consolidado_path = tmp_path / "inexistente.csv"
    result = generate(
        consolidado_path=consolidado_path,
        db_path=db_path,
        quiet=True,
    )
    assert result["errors"] > 0 or result["total"] == 0


def test_generate_preserva_cnpj_existente(tmp_path):
    db_path = tmp_path / "empresas.db"
    zip_path = tmp_path / "empresas0.zip"
    _criar_zip_emprcsv(zip_path, [
        '00000000;"Ambev S.A.";;',
    ])
    _construir_db([zip_path], db_path)

    consolidado_path = tmp_path / "emissores_consolidado.csv"
    _escrever_csv(consolidado_path, [
        {
            "no_emissor_padronizado": "AMBEV",
            "no_emissor_fitch": "",
            "no_emissor_moodys": "",
            "no_emissor_standard_and_poors": "",
            "cnpj_emissor": "99999999000199",
        },
    ])

    result = generate(
        consolidado_path=consolidado_path,
        db_path=db_path,
        rebuild_db=False,
        quiet=True,
    )

    assert result["matched"] == 0

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["cnpj_emissor"] == "99999999000199"


def test_generate_trailing_comma_no_crash(tmp_path):
    """CSV com coluna extra não crasha."""
    db_path = tmp_path / "empresas.db"
    zip_path = tmp_path / "empresas0.zip"
    _criar_zip_emprcsv(zip_path, [
        '00000000;"Ambev S.A.";;',
    ])
    _construir_db([zip_path], db_path)

    consolidado_path = tmp_path / "emissores_consolidado.csv"
    consolidado_path.write_text(
        "no_emissor_padronizado,no_emissor_fitch,no_emissor_moodys,no_emissor_standard_and_poors,no_emissor_austin,no_emissor_liberum,cnpj_emissor,\n"
        "AMBEV,Ambev S.A.,,,,\n",
        encoding="utf-8",
    )

    result = generate(
        consolidado_path=consolidado_path,
        db_path=db_path,
        rebuild_db=False,
        quiet=True,
    )

    assert result["matched"] == 1

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["cnpj_emissor"] == "00000000000191"
