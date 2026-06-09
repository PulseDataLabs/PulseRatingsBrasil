import csv
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.preencher_cnpj_api import (
    _limpar_cnpj,
    _obter_nome_busca,
    _gerar_variantes_busca,
    _matches,
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
        "no_emissor_padronizado": "AMBEV",
        "no_emissor_fitch": "Ambev Fitch",
        "no_emissor_moodys": "Ambev Moodys",
        "no_emissor_standard_and_poors": "Ambev SP",
    }
    assert _obter_nome_busca(row) == "Ambev Fitch"


def test_obter_nome_busca_fallback():
    row = {
        "no_emissor_padronizado": "VALE",
        "no_emissor_fitch": "",
        "no_emissor_moodys": "Vale S.A.",
        "no_emissor_standard_and_poors": "",
    }
    assert _obter_nome_busca(row) == "Vale S.A."


def test_obter_nome_busca_somente_padronizado():
    row = {
        "no_emissor_padronizado": "EMPRESA",
        "no_emissor_fitch": "",
        "no_emissor_moodys": "",
        "no_emissor_standard_and_poors": "",
    }
    assert _obter_nome_busca(row) == "EMPRESA"


# ── _gerar_variantes_busca ─────────────────────────────────────────────────────


def test_gerar_variantes_ordem():
    """Nome original primeiro, depois sem sufixos, depois +curto, depois nome_pad."""
    v = _gerar_variantes_busca("Ambev S.A.", "AMBEV")
    assert v[0] == "Ambev S.A."
    assert "Ambev" in v
    assert "AMBEV" in v


def test_gerar_variantes_dedup():
    """Remove duplicatas e strings muito curtas."""
    v = _gerar_variantes_busca("Ab", "AMBEV")
    assert "Ab" not in v  # len < 3 descartado


def test_gerar_variantes_nome_curto():
    """Nome com 2 palavras: só original + sem sufixo + nome_pad."""
    v = _gerar_variantes_busca("Vale S.A.", "VALE")
    assert len(v) >= 2
    assert v[0] == "Vale S.A."


def test_gerar_variantes_nome_longo():
    """Nome com 4+ palavras: inclui variante com 2 e 3 palavras."""
    v = _gerar_variantes_busca("Coca Cola FEMSA Brasil Ltda.", "COCA COLA FEMSA")
    first_words = [x for x in v if len(x.split()) <= 3]
    assert any(x == "Coca Cola" for x in first_words)
    assert any("Coca Cola FEMSA" in x for x in first_words)


# ── _matches ────────────────────────────────────────────────────────────────────


def test_matches_exato():
    """normalizar exato bate."""
    assert _matches("Ambev S.A.", "AMBEV") is True


def test_matches_startswith():
    """hit normalizado começa com nome_pad."""
    assert _matches("Ambev Brasil Bebidas Ltda.", "AMBEV") is True


def test_matches_startswith_reverso():
    """nome_pad começa com hit normalizado."""
    assert _matches("AMBEV", "AMBEV S.A.") is True


def test_matches_token_overlap():
    """Todas as palavras de nome_pad estão no hit."""
    assert _matches("Coca Cola FEMSA Brasil Ltda.", "COCA COLA FEMSA") is True


def test_matches_token_overlap_insuficiente():
    """Token único não basta para overlap."""
    assert _matches("Qualquer Coisa Ltda.", "EMPRESA") is False


def test_matches_vazio():
    assert _matches("", "AMBEV") is False
    assert _matches("Ambev S.A.", "") is False


# ── generate ───────────────────────────────────────────────────────────────────


@pytest.fixture
def consolidado_path(tmp_path):
    path = tmp_path / "emissores_consolidado.csv"
    _escrever_csv(path, [
        {
            "no_emissor_padronizado": "AMBEV",
            "no_emissor_fitch": "Ambev S.A.",
            "no_emissor_moodys": "",
            "no_emissor_standard_and_poors": "",
            "cnpj_emissor": "",
        },
        {
            "no_emissor_padronizado": "VALE",
            "no_emissor_fitch": "",
            "no_emissor_moodys": "Vale S.A.",
            "no_emissor_standard_and_poors": "",
            "cnpj_emissor": "",
        },
        {
            "no_emissor_padronizado": "EMPRESA",
            "no_emissor_fitch": "Empresa X Ltda.",
            "no_emissor_moodys": "",
            "no_emissor_standard_and_poors": "",
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

    cnpjs = {r["no_emissor_padronizado"]: r["cnpj_emissor"] for r in rows}
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
            "no_emissor_padronizado": "AMBEV",
            "no_emissor_fitch": "Ambev S.A.",
            "no_emissor_moodys": "",
            "no_emissor_standard_and_poors": "",
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
        "no_emissor_padronizado,no_emissor_fitch,no_emissor_moodys,no_emissor_standard_and_poors,cnpj_emissor,\n"
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
