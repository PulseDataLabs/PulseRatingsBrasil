import csv
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.preencher_cnpj_cvm import (
    _limpar_cnpj,
    _carregar_lookup_cias,
    _carregar_lookup_fundos,
    generate,
)


def _escrever_csv(path: Path, rows: list[dict], delimiter: str = ","):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


# ── _limpar_cnpj ──────────────────────────────────────────────────────────────


def test_limpar_cnpj():
    assert _limpar_cnpj("00.000.000/0001-91") == "00000000000191"
    assert _limpar_cnpj("") == ""
    assert _limpar_cnpj("12.345.678/0001-99") == "12345678000199"
    assert _limpar_cnpj(None) == ""


# ── _carregar_lookup_cias ─────────────────────────────────────────────────────


def test_lookup_cias_simples(tmp_path):
    path = tmp_path / "cad_cia_aberta.csv"
    _escrever_csv(path, [
        {"CNPJ_CIA": "00.000.000/0001-91", "DENOM_SOCIAL": "Ambev S.A."},
        {"CNPJ_CIA": "11.111.111/0001-11", "DENOM_SOCIAL": "Vale S.A."},
    ], delimiter=";")
    result = _carregar_lookup_cias(path)
    assert result["AMBEV"] == "00000000000191"
    assert result["VALE"] == "11111111000111"


def test_lookup_cias_ambiguo_ignorado(tmp_path):
    path = tmp_path / "cad_cia_aberta.csv"
    _escrever_csv(path, [
        {"CNPJ_CIA": "00.000.000/0001-91", "DENOM_SOCIAL": "ABC Brasil S.A."},
        {"CNPJ_CIA": "11.111.111/0001-11", "DENOM_SOCIAL": "ABC Brasil Ltda."},
    ], delimiter=";")
    result = _carregar_lookup_cias(path)
    assert "ABC BRASIL" not in result


def test_lookup_cias_cnpj_invalido_ignorado(tmp_path):
    path = tmp_path / "cad_cia_aberta.csv"
    _escrever_csv(path, [
        {"CNPJ_CIA": "123", "DENOM_SOCIAL": "Empresa X S.A."},
        {"CNPJ_CIA": "", "DENOM_SOCIAL": "Empresa Y S.A."},
    ], delimiter=";")
    result = _carregar_lookup_cias(path)
    assert result == {}


# ── _carregar_lookup_fundos ───────────────────────────────────────────────────


def test_lookup_fundos_admin(tmp_path):
    path = tmp_path / "cad_fi.csv"
    _escrever_csv(path, [
        {
            "CNPJ_ADMIN": "00.000.000/0001-91",
            "ADMIN": "Banco Bradesco S.A.",
            "CPF_CNPJ_GESTOR": "",
            "GESTOR": "",
        },
    ], delimiter=";")
    result = _carregar_lookup_fundos(path)
    assert result["BANCO BRADESCO"] == "00000000000191"


def test_lookup_fundos_gestor(tmp_path):
    path = tmp_path / "cad_fi.csv"
    _escrever_csv(path, [
        {
            "CNPJ_ADMIN": "",
            "ADMIN": "",
            "CPF_CNPJ_GESTOR": "99.888.777/0001-66",
            "GESTOR": "Western Asset Management",
        },
    ], delimiter=";")
    result = _carregar_lookup_fundos(path)
    assert "WESTERN ASSET MANAGEMENT" in result
    assert result["WESTERN ASSET MANAGEMENT"] == "99888777000166"


# ── generate (com mock HTTP) ────────────────────────────────────────────────────


@pytest.fixture
def consolidado_path(tmp_path):
    path = tmp_path / "emissores_consolidado.csv"
    _escrever_csv(path, [
        {
            "nome_emissor_padronizado": "AMBEV",
            "nome_emissor_fitch": "Ambev S.A.",
            "nome_emissor_moodys": "",
            "nome_emissor_standard_and_poors": "",
            "cnpj_emissor": "",
        },
        {
            "nome_emissor_padronizado": "VALE",
            "nome_emissor_fitch": "",
            "nome_emissor_moodys": "Vale S.A.",
            "nome_emissor_standard_and_poors": "",
            "cnpj_emissor": "",
        },
        {
            "nome_emissor_padronizado": "BANCO BRADESCO",
            "nome_emissor_fitch": "",
            "nome_emissor_moodys": "",
            "nome_emissor_standard_and_poors": "Banco Bradesco S.A.",
            "cnpj_emissor": "",
        },
        {
            "nome_emissor_padronizado": "EMPRESA",
            "nome_emissor_fitch": "Empresa X Ltda.",
            "nome_emissor_moodys": "",
            "nome_emissor_standard_and_poors": "",
            "cnpj_emissor": "",
        },
    ])
    return path


def _mock_response(content: bytes, status: int = 200):
    mock_resp = MagicMock()
    mock_resp.content = content
    mock_resp.status_code = status
    mock_resp.raise_for_status = MagicMock()
    if status >= 400:
        mock_resp.raise_for_status.side_effect = Exception("HTTP error")
    return mock_resp


CIA_CSV = (
    "CNPJ_CIA;DENOM_SOCIAL\n"
    "00.000.000/0001-91;Ambev S.A.\n"
    "11.111.111/0001-11;Vale S.A.\n"
)

FI_CSV = (
    "CNPJ_ADMIN;ADMIN;CPF_CNPJ_GESTOR;GESTOR\n"
    "22.222.222/0001-22;Banco Bradesco S.A.;;\n"
)


@patch("scripts.preencher_cnpj_cvm.requests.get")
def test_generate_preenche_cnpj(mock_get, consolidado_path, tmp_path):
    def side_effect(url, **kwargs):
        if "cad_cia_aberta" in url:
            return _mock_response(CIA_CSV.encode("latin-1"))
        if "cad_fi" in url:
            return _mock_response(FI_CSV.encode("latin-1"))
        return _mock_response(b"", 404)

    mock_get.side_effect = side_effect

    result = generate(
        consolidado_path=consolidado_path,
        cache_dir=tmp_path / "cvm_cache",
    )

    assert result["total"] == 4
    assert result["matched"] == 3
    assert result["unmatched"] == 1

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    cnpjs = {r["nome_emissor_padronizado"]: r["cnpj_emissor"] for r in rows}
    assert cnpjs["AMBEV"] == "00000000000191"
    assert cnpjs["VALE"] == "11111111000111"
    assert cnpjs["BANCO BRADESCO"] == "22222222000122"
    assert cnpjs["EMPRESA"] == ""  # not in CVM data


@patch("scripts.preencher_cnpj_cvm.requests.get")
def test_generate_preserva_cnpj_existente(mock_get, consolidado_path, tmp_path):
    _escrever_csv(consolidado_path, [
        {
            "nome_emissor_padronizado": "AMBEV",
            "nome_emissor_fitch": "Ambev S.A.",
            "nome_emissor_moodys": "",
            "nome_emissor_standard_and_poors": "",
            "cnpj_emissor": "99999999000199",
        },
    ])

    def side_effect(url, **kwargs):
        if "cad_cia_aberta" in url:
            return _mock_response(CIA_CSV.encode("latin-1"))
        return _mock_response(b"", 404)

    mock_get.side_effect = side_effect

    result = generate(
        consolidado_path=consolidado_path,
        cache_dir=tmp_path / "cvm_cache",
    )

    assert result["matched"] == 0

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows[0]["cnpj_emissor"] == "99999999000199"


@patch("scripts.preencher_cnpj_cvm.requests.get")
def test_generate_sem_cvm_data(mock_get, consolidado_path, tmp_path):
    mock_get.return_value = _mock_response(b"", 500)
    result = generate(
        consolidado_path=consolidado_path,
        cache_dir=tmp_path / "cvm_cache",
    )
    assert result["matched"] == 0
    assert result["unmatched"] == 4
