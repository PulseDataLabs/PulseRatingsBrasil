import csv
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.preencher_cnpj_api import (
    _limpar_cnpj,
    _obter_nome_busca,
    generate,
)


def _escrever_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ── _limpar_cnpj ──────────────────────────────────────────────────────────────


def test_limpar_cnpj():
    assert _limpar_cnpj("00.000.000/0001-91") == "00000000000191"
    assert _limpar_cnpj("") == ""
    assert _limpar_cnpj(None) == ""


# ── _obter_nome_busca ──────────────────────────────────────────────────────────


def test_obter_nome_busca_prioridade():
    row = {
        "nome_emissor_padronizado": "AMBEV",
        "nome_emissor_fitch": "Ambev Fitch",
        "nome_emissor_moodys": "Ambev Moodys",
        "nome_emissor_standard_and_poors": "Ambev SP",
    }
    assert _obter_nome_busca(row) == "Ambev Fitch"


def test_obter_nome_busca_fallback():
    row = {
        "nome_emissor_padronizado": "VALE",
        "nome_emissor_fitch": "",
        "nome_emissor_moodys": "Vale S.A.",
        "nome_emissor_standard_and_poors": "",
    }
    assert _obter_nome_busca(row) == "Vale S.A."


def test_obter_nome_busca_somente_padronizado():
    row = {
        "nome_emissor_padronizado": "EMPRESA",
        "nome_emissor_fitch": "",
        "nome_emissor_moodys": "",
        "nome_emissor_standard_and_poors": "",
    }
    assert _obter_nome_busca(row) == "EMPRESA"


# ── generate ───────────────────────────────────────────────────────────────────


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
            "nome_emissor_padronizado": "EMPRESA",
            "nome_emissor_fitch": "Empresa X Ltda.",
            "nome_emissor_moodys": "",
            "nome_emissor_standard_and_poors": "",
            "cnpj_emissor": "",
        },
    ])
    return path


def _fake_client(results: list[dict]):
    """Return a mock Client.search that returns the given results."""

    def search(query, per_page=5):
        return {"results": results}

    client = MagicMock()
    client.search = MagicMock(side_effect=search)
    return client


@patch("scripts.preencher_cnpj_api.os.environ.get")
@patch("cnpjaberto.Client")
def test_generate_com_api_key(mock_client_cls, mock_environ_get, consolidado_path):
    mock_environ_get.return_value = "fake-key"

    mock_client_instance = _fake_client([
        {"cnpj": "00.000.000/0001-91", "razao_social": "Ambev S.A."},
        {"cnpj": "", "razao_social": ""},
    ])
    mock_client_cls.return_value.__enter__.return_value = mock_client_instance

    result = generate(
        consolidado_path=consolidado_path,
        rate_limit=0.0,
    )

    assert result["matched"] == 1
    assert result["unmatched"] == 2

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    cnpjs = {r["nome_emissor_padronizado"]: r["cnpj_emissor"] for r in rows}
    assert cnpjs["AMBEV"] == "00000000000191"
    assert cnpjs["VALE"] == ""
    assert cnpjs["EMPRESA"] == ""


@patch("scripts.preencher_cnpj_api.os.environ.get")
def test_generate_sem_api_key(mock_environ_get, consolidado_path):
    mock_environ_get.return_value = ""
    result = generate(consolidado_path=consolidado_path)
    assert result["skipped_no_key"] is True
    assert result["matched"] == 0

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert all(r["cnpj_emissor"] == "" for r in rows)


@patch("scripts.preencher_cnpj_api.os.environ.get")
def test_generate_preserva_cnpj_existente(mock_environ_get, consolidado_path):
    mock_environ_get.return_value = "fake-key"
    _escrever_csv(consolidado_path, [
        {
            "nome_emissor_padronizado": "AMBEV",
            "nome_emissor_fitch": "Ambev S.A.",
            "nome_emissor_moodys": "",
            "nome_emissor_standard_and_poors": "",
            "cnpj_emissor": "99999999000199",
        },
    ])

    with patch("cnpjaberto.Client") as mock_client_cls:
        mock_client_instance = _fake_client([])
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        result = generate(
            consolidado_path=consolidado_path,
            rate_limit=0.0,
        )

    assert result["matched"] == 0

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["cnpj_emissor"] == "99999999000199"


@patch("scripts.preencher_cnpj_api.os.environ.get")
@patch("cnpjaberto.Client")
def test_generate_com_trailing_comma(mock_client_cls, mock_environ_get, tmp_path):
    """CSV com coluna extra (trailing comma) não deve crashar no Py3.13."""
    mock_environ_get.return_value = "fake-key"
    path = tmp_path / "emissores_consolidado.csv"
    path.write_text(
        "nome_emissor_padronizado,nome_emissor_fitch,nome_emissor_moodys,nome_emissor_standard_and_poors,cnpj_emissor,\n"
        "AMBEV,Ambev S.A.,,,,\n"
        "EMPRESA,Empresa X Ltda.,,,,\n",
        encoding="utf-8",
    )

    mock_client_instance = _fake_client([
        {"cnpj": "00.000.000/0001-91", "razao_social": "Ambev S.A."},
    ])
    mock_client_cls.return_value.__enter__.return_value = mock_client_instance

    result = generate(
        consolidado_path=path,
        rate_limit=0.0,
    )

    assert result["matched"] == 1
    assert result["unmatched"] == 1
    assert result["errors"] == 0

    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["cnpj_emissor"] == "00000000000191"


@patch("scripts.preencher_cnpj_api.os.environ.get")
def test_generate_dry_run(mock_environ_get, consolidado_path):
    mock_environ_get.return_value = "fake-key"
    result = generate(
        consolidado_path=consolidado_path,
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["pendentes"] == 3

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert all(r["cnpj_emissor"] == "" for r in rows)
