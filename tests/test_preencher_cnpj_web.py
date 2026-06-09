import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.preencher_cnpj_web import (
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
            "no_emissor_padronizado": "PETROBRAS",
            "no_emissor_fitch": "Petrobras",
            "no_emissor_moodys": "",
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


def _fake_search_results(results_map: dict[str, list[dict]]):
    """Return a mock DDGS.text that returns predefined results per query."""
    ddgs = MagicMock()
    ddgs.text = MagicMock(side_effect=lambda keywords, max_results=5: results_map.get(keywords, []))
    return ddgs


@patch("ddgs.DDGS")
def test_generate_match_simples(mock_ddgs_cls, consolidado_path):
    """CNPJ único no snippet deve ser usado."""
    mock_ddgs_cls.return_value.__enter__.return_value = _fake_search_results({
        '"Ambev S.A." CNPJ': [
            {"title": "Ambev S.A. 00.000.000/0001-91", "body": "Ambev S.A. CNPJ 00.000.000/0001-91", "href": ""},
            {"title": "site", "body": "outro texto", "href": ""},
        ],
    })

    result = generate(
        consolidado_path=consolidado_path,
        rate_limit=0.0,
    )

    assert result["matched"] == 1
    assert result["unmatched"] == 3
    assert result["errors"] == 0

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cnpjs = {r["no_emissor_padronizado"]: r["cnpj_emissor"] for r in rows}
    assert cnpjs["AMBEV"] == "00000000000191"
    assert cnpjs["VALE"] == ""
    assert cnpjs["EMPRESA"] == ""


@patch("ddgs.DDGS")
def test_generate_multi_cnpj_desambiguacao(mock_ddgs_cls, consolidado_path):
    """Múltiplos CNPJs nos resultados: usa o que vier num snippet que normalize como nome_pad."""
    mock_ddgs_cls.return_value.__enter__.return_value = _fake_search_results({
        '"Vale S.A." CNPJ': [
            {"title": "Vale S.A. 00.000.000/0001-91", "body": "Vale S.A. CNPJ 00.000.000/0001-91", "href": ""},
            {"title": "Vale S.A.", "body": "outra empresa 11.111.111/0001-00", "href": ""},
        ],
    })

    result = generate(
        consolidado_path=consolidado_path,
        rate_limit=0.0,
    )

    assert result["matched"] == 1
    assert result["unmatched"] == 3
    assert result["errors"] == 0

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cnpjs = {r["no_emissor_padronizado"]: r["cnpj_emissor"] for r in rows}
    assert cnpjs["VALE"] == "00000000000191"


@patch("ddgs.DDGS")
def test_generate_sem_resultados(mock_ddgs_cls, consolidado_path):
    """Sem resultados de busca → unmatched."""
    mock_ddgs_cls.return_value.__enter__.return_value = _fake_search_results({})

    result = generate(
        consolidado_path=consolidado_path,
        rate_limit=0.0,
    )

    assert result["matched"] == 0
    assert result["unmatched"] == 4
    assert result["errors"] == 0


@patch("ddgs.DDGS")
def test_generate_erro_busca(mock_ddgs_cls, consolidado_path):
    """Erro na busca → contabilizado como erro."""
    ddgs = MagicMock()
    ddgs.text = MagicMock(side_effect=Exception("timeout"))
    mock_ddgs_cls.return_value.__enter__.return_value = ddgs

    result = generate(
        consolidado_path=consolidado_path,
        rate_limit=0.0,
    )

    assert result["matched"] == 0
    assert result["errors"] == 4


@patch("ddgs.DDGS")
def test_generate_multi_cnpj_ambiguo_sem_desambiguar(mock_ddgs_cls, consolidado_path):
    """Múltiplos CNPJs sem snippet que normalize = nome_pad → unmatched."""
    # Só o primeiro pendente ("Ambev S.A.") vai buscar;
    # como o title "SomeSite" não normaliza para "AMBEV", é ambíguo
    mock_ddgs_cls.return_value.__enter__.return_value = _fake_search_results({
        '"Ambev S.A." CNPJ': [
            {"title": "SomeSite", "body": "CNPJ 00.000.000/0001-91 e 11.111.111/0001-00", "href": ""},
        ],
    })

    result = generate(
        consolidado_path=consolidado_path,
        rate_limit=0.0,
    )

    assert result["matched"] == 0
    assert result["unmatched"] == 4
    assert result["errors"] == 0


@patch("ddgs.DDGS")
def test_generate_preserva_cnpj_existente(mock_ddgs_cls, consolidado_path):
    """Emissor já com CNPJ não é re-processado."""
    _escrever_csv(consolidado_path, [
        {
            "no_emissor_padronizado": "AMBEV",
            "no_emissor_fitch": "Ambev S.A.",
            "no_emissor_moodys": "",
            "no_emissor_standard_and_poors": "",
            "cnpj_emissor": "99999999000199",
        },
    ])

    ddgs = MagicMock()
    ddgs.text = MagicMock(side_effect=Exception("nao deve ser chamado"))
    mock_ddgs_cls.return_value.__enter__.return_value = ddgs

    result = generate(
        consolidado_path=consolidado_path,
        rate_limit=0.0,
    )

    assert result["matched"] == 0

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["cnpj_emissor"] == "99999999000199"


@patch("ddgs.DDGS")
def test_generate_consolidado_inexistente(mock_ddgs_cls, tmp_path):
    """Caminho inexistente retorna sem erro."""
    path = tmp_path / "nao_existe.csv"
    result = generate(
        consolidado_path=path,
        rate_limit=0.0,
    )
    assert result["total"] == 0
    assert result["matched"] == 0


@patch("ddgs.DDGS")
def test_generate_salvamento_incremental(mock_ddgs_cls, consolidado_path):
    """CSV é salvo a cada CNPJ encontrado (não apenas no fim)."""
    mock_ddgs_cls.return_value.__enter__.return_value = _fake_search_results({
        '"Ambev S.A." CNPJ': [
            {"title": "Ambev S.A. 00.000.000/0001-91", "body": "Ambev S.A.", "href": ""},
        ],
        '"Vale S.A." CNPJ': [
            {"title": "Vale S.A.", "body": "Vale S.A. 11.111.111/0001-00", "href": ""},
        ],
        '"Petrobras" CNPJ': [
            {"title": "Petrobras 22.222.222/0001-00", "body": "Petrobras", "href": ""},
        ],
        '"Empresa X Ltda." CNPJ': [
            {"title": "Empresa X 33.333.333/0001-00", "body": "Empresa X Ltda.", "href": ""},
        ],
    })

    result = generate(
        consolidado_path=consolidado_path,
        rate_limit=0.0,
    )

    assert result["matched"] == 4

    with open(consolidado_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cnpjs = {r["no_emissor_padronizado"]: r["cnpj_emissor"] for r in rows}
    assert cnpjs["AMBEV"] == "00000000000191"
    assert cnpjs["VALE"] == "11111111000100"
    assert cnpjs["PETROBRAS"] == "22222222000100"
    assert cnpjs["EMPRESA"] == "33333333000100"


@patch("ddgs.DDGS")
def test_generate_com_trailing_comma(mock_ddgs_cls, tmp_path):
    """CSV com coluna extra (trailing comma) não deve crashar no Py3.13."""
    path = tmp_path / "emissores_consolidado.csv"
    path.write_text(
        "no_emissor_padronizado,no_emissor_fitch,no_emissor_moodys,no_emissor_standard_and_poors,cnpj_emissor,\n"
        "AMBEV,Ambev S.A.,,,,\n"
        "EMPRESA,Empresa X Ltda.,,,,\n",
        encoding="utf-8",
    )

    mock_ddgs_cls.return_value.__enter__.return_value = _fake_search_results({
        '"Ambev S.A." CNPJ': [
            {"title": "Ambev S.A. 00.000.000/0001-91", "body": "Ambev S.A. CNPJ", "href": ""},
        ],
    })

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
