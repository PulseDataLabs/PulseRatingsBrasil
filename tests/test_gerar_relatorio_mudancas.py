import pytest
from scripts.gerar_relatorio_mudancas import (
    normalizar_rating,
    normalizar_outlook,
    comparar_snapshots,
    gerar_markdown,
)


def test_normalizar_rating():
    assert normalizar_rating("AAA.br")[0] == "AAA"
    assert normalizar_rating("AAA.br")[1] == 1

    assert normalizar_rating("brAA+")[0] == "AA+"
    assert normalizar_rating("brAA+")[1] == 2

    assert normalizar_rating("AA-(bra)")[0] == "AA-"
    assert normalizar_rating("AA-(bra)")[1] == 4

    assert normalizar_rating("brBBB-")[0] == "BBB-"
    assert normalizar_rating("brBBB-")[1] == 10

    assert normalizar_rating("brD")[0] == "D"
    assert normalizar_rating("brD")[1] == 22

    assert normalizar_rating("QG2+")[0] == "QG2+"
    assert normalizar_rating("QG2+")[1] == 2

    assert normalizar_rating("")[1] is None
    assert normalizar_rating(None)[1] is None


def test_normalizar_outlook():
    assert normalizar_outlook("Perspectiva estável") == "Estável"
    assert normalizar_outlook("Estável") == "Estável"
    assert normalizar_outlook("Negativa") == "Negativa"
    assert normalizar_outlook("Positiva") == "Positiva"
    assert normalizar_outlook("Em observação positiva") == "Em Observação"
    assert normalizar_outlook(None) == "Estável"


def test_comparar_snapshots_upgrade_downgrade():
    rows = [
        # Captura Atual
        {
            "dt_captura": "2026-08-19",
            "agencia": "S&P",
            "no_emissor_padronizado": "EMPRESA A",
            "no_tipo_rating": "Corporativo",
            "de_rating_br": "brAAA",
            "de_outlook": "Estável",
            "dt_acao_rating": "2026-08-19",
        },
        {
            "dt_captura": "2026-08-19",
            "agencia": "Moody's",
            "no_emissor_padronizado": "EMPRESA B",
            "no_tipo_rating": "Corporativo",
            "de_rating_br": "BB.br",
            "de_outlook": "Negativa",
            "dt_acao_rating": "2026-08-19",
        },
        {
            "dt_captura": "2026-08-19",
            "agencia": "Fitch",
            "no_emissor_padronizado": "NOVA EMPRESA",
            "no_tipo_rating": "Corporativo",
            "de_rating_br": "A(bra)",
            "de_outlook": "Estável",
            "dt_acao_rating": "2026-08-19",
        },
        # Captura Anterior
        {
            "dt_captura": "2026-08-18",
            "agencia": "S&P",
            "no_emissor_padronizado": "EMPRESA A",
            "no_tipo_rating": "Corporativo",
            "de_rating_br": "brAA+",
            "de_outlook": "Estável",
            "dt_acao_rating": "2026-08-18",
        },
        {
            "dt_captura": "2026-08-18",
            "agencia": "Moody's",
            "no_emissor_padronizado": "EMPRESA B",
            "no_tipo_rating": "Corporativo",
            "de_rating_br": "BBB-.br",
            "de_outlook": "Estável",
            "dt_acao_rating": "2026-08-18",
        },
        {
            "dt_captura": "2026-08-18",
            "agencia": "Fitch",
            "no_emissor_padronizado": "EMPRESA RETIRADA",
            "no_tipo_rating": "Corporativo",
            "de_rating_br": "AAA(bra)",
            "de_outlook": "Estável",
            "dt_acao_rating": "2026-08-18",
        },
    ]

    res = comparar_snapshots(rows, "emissores", ["agencia", "no_emissor_padronizado", "no_tipo_rating"])

    assert len(res["upgrades"]) == 1
    assert res["upgrades"][0]["emissor"] == "EMPRESA A"
    assert res["upgrades"][0]["rating_anterior"] == "brAA+"
    assert res["upgrades"][0]["rating_atual"] == "brAAA"

    assert len(res["downgrades"]) == 1
    assert res["downgrades"][0]["emissor"] == "EMPRESA B"
    assert res["downgrades"][0]["rating_anterior"] == "BBB-.br"
    assert res["downgrades"][0]["rating_atual"] == "BB.br"

    assert len(res["novos"]) == 1
    assert res["novos"][0]["emissor"] == "NOVA EMPRESA"

    assert len(res["retirados"]) == 1
    assert res["retirados"][0]["emissor"] == "EMPRESA RETIRADA"


def test_gerar_markdown():
    relatorio = {
        "dt_atual": "2026-08-19",
        "dt_anterior": "2026-08-18",
        "resumo": {
            "upgrades_emissores": 1,
            "upgrades_emissoes": 0,
            "total_upgrades": 1,
            "downgrades_emissores": 0,
            "downgrades_emissoes": 1,
            "total_downgrades": 1,
            "total_novos": 1,
            "total_outlooks": 0,
            "total_retirados": 0,
        },
        "emissores": {
            "upgrades": [
                {
                    "agencia": "S&P",
                    "emissor": "TESTE S.A.",
                    "instrumento": "Corporativo",
                    "rating_anterior": "brAA+",
                    "rating_atual": "brAAA",
                    "outlook_atual": "Estável",
                    "dt_acao": "2026-08-19",
                }
            ],
            "downgrades": [],
            "novos": [],
            "outlooks": [],
            "retirados": [],
        },
        "emissoes": {
            "upgrades": [],
            "downgrades": [
                {
                    "agencia": "Fitch",
                    "emissor": "FIDC TESTE",
                    "instrumento": "Senior",
                    "rating_anterior": "AAA(bra)",
                    "rating_atual": "AA(bra)",
                    "outlook_atual": "Negativa",
                    "dt_acao": "2026-08-19",
                }
            ],
            "novos": [],
            "outlooks": [],
            "retirados": [],
        },
    }

    md = gerar_markdown(relatorio)
    assert "# 📊 Relatório de Movimentações de Ratings (2026-08-19)" in md
    assert "TESTE S.A." in md
    assert "FIDC TESTE" in md
    assert "Upgrades (Elevações)" in md
    assert "Downgrades (Rebaixamentos)" in md
