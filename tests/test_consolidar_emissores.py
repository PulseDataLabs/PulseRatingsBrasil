import csv
import tempfile
from pathlib import Path

from scripts.consolidar_emissores import (
    COLUNAS,
    normalizar,
    carregar_emissores_fonte,
    carregar_consolidado_existente,
    consolidar,
)


def _csv_bytes(rows: list[dict]) -> str:
    buf = []
    writer = csv.DictWriter(buf := [""], fieldnames=list(rows[0].keys()))
    # workaround: build string manually
    header = ",".join(rows[0].keys())
    lines = [header]
    for r in rows:
        lines.append(",".join(r.values()))
    return "\n".join(lines) + "\n"


def _escrever_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ── normalizar ─────────────────────────────────────────────────────────────────


def test_normalizar_sa():
    assert normalizar("Ambev S.A.") == "AMBEV"
    assert normalizar("Banco Bradesco S.A.") == "BANCO BRADESCO"
    assert normalizar("Vale S.A.") == "VALE"
    assert normalizar("Ambev S/A") == "AMBEV"
    assert normalizar("Ambev LTDA") == "AMBEV"
    assert normalizar("Ambev Ltda.") == "AMBEV"
    assert normalizar("Empresa ME") == "EMPRESA"


def test_normalizar_acentos():
    assert normalizar("Itaú Unibanco") == "ITAU UNIBANCO"
    assert normalizar("São Paulo") == "SAO PAULO"
    assert normalizar("Araújo") == "ARAUJO"
    assert normalizar("João da Silva Ltda.") == "JOAO SILVA"
    assert normalizar("Coração") == "CORACAO"
    assert normalizar("AÇÚCAR") == "ACUCAR"


def test_normalizar_parenteses():
    assert normalizar("Companhia Siderurgica Nacional (CSN)") == "COMPANHIA SIDERURGICA NACIONAL"
    assert normalizar("Empresa (Brasil) S.A.") == "EMPRESA"
    assert normalizar("Nome (Antigo) Novo") == "NOME NOVO"


def test_normalizar_palavras_genericas():
    assert normalizar("Banco do Brasil S.A.") == "BANCO"
    assert normalizar("Cia de Bebidas e Alimentos") == "CIA BEBIDAS ALIMENTOS"
    assert normalizar("Empresa no Brasil Ltda.") == "EMPRESA"
    assert normalizar("Casa & Comercio") == "CASA COMERCIO"


def test_normalizar_b3():
    assert normalizar("B3 S.A. – Brasil, Bolsa, Balcão") == "B3"
    assert normalizar("B3 S.A. - Brasil, Bolsa, Balcao") == "B3"
    assert normalizar("B3 S/A – Brasil Bolsa Balcao") == "B3"


def test_normalizar_vazios():
    assert normalizar("") == ""
    assert normalizar("   ") == ""
    assert normalizar(None) == ""


# ── carregar_emissores_fonte ───────────────────────────────────────────────────


def test_carregar_csv_normal(tmp_path):
    path = tmp_path / "fonte.csv"
    _escrever_csv(path, [
        {"no_entidade": "Ambev S.A.", "link": "http://a"},
        {"no_entidade": "Vale S.A.", "link": "http://b"},
    ])
    result = carregar_emissores_fonte(path)
    assert result == {"Ambev S.A.": "AMBEV", "Vale S.A.": "VALE"}


def test_carregar_csv_vazio(tmp_path):
    path = tmp_path / "vazio.csv"
    _escrever_csv(path, [{"no_entidade": "", "link": ""}])
    result = carregar_emissores_fonte(path)
    assert result == {}


def test_carregar_csv_inexistente(tmp_path):
    path = tmp_path / "nao_existe.csv"
    result = carregar_emissores_fonte(path)
    assert result == {}


# ── carregar_consolidado_existente ─────────────────────────────────────────────


def test_carregar_consolidado_existente_normal(tmp_path):
    path = tmp_path / "consolidado.csv"
    _escrever_csv(path, [
        {
            "nome_emissor_padronizado": "AMBEV",
            "nome_emissor_fitch": "Ambev S.A.",
            "nome_emissor_moodys": "",
            "nome_emissor_standard_and_poors": "",
            "cnpj_emissor": "12345678000199",
        },
    ])
    result = carregar_consolidado_existente(path)
    assert "AMBEV" in result
    assert result["AMBEV"]["cnpj_emissor"] == "12345678000199"


def test_carregar_consolidado_inexistente(tmp_path):
    result = carregar_consolidado_existente(tmp_path / "nope.csv")
    assert result == {}


# ── consolidar ─────────────────────────────────────────────────────────────────


def test_consolidar_simples(tmp_path):
    fitch = tmp_path / "fitch.csv"
    _escrever_csv(fitch, [{"no_entidade": "Ambev S.A.", "link": ""}])

    moodys = tmp_path / "moodys.csv"
    _escrever_csv(moodys, [{"no_entidade": "", "link": ""}])

    sp = tmp_path / "sp.csv"
    _escrever_csv(sp, [{"no_entidade": "", "link": ""}])

    output = tmp_path / "out.csv"
    consolidar(fitch, moodys, sp, output)

    with open(output, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["nome_emissor_padronizado"] == "AMBEV"
    assert rows[0]["nome_emissor_fitch"] == "Ambev S.A."
    assert rows[0]["nome_emissor_moodys"] == ""


def test_consolidar_mesmo_emissor_2_fontes(tmp_path):
    fitch = tmp_path / "fitch.csv"
    _escrever_csv(fitch, [{"no_entidade": "Ambev S.A.", "link": ""}])

    moodys = tmp_path / "moodys.csv"
    _escrever_csv(moodys, [{"no_entidade": "", "link": ""}])

    sp = tmp_path / "sp.csv"
    _escrever_csv(sp, [{"no_entidade": "AMBEV S.A.", "link": ""}])

    output = tmp_path / "out.csv"
    consolidar(fitch, moodys, sp, output)

    with open(output, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["nome_emissor_fitch"] == "Ambev S.A."
    assert rows[0]["nome_emissor_standard_and_poors"] == "AMBEV S.A."


def test_consolidar_merge_preserva_cnpj(tmp_path):
    output = tmp_path / "out.csv"
    _escrever_csv(output, [
        {
            "nome_emissor_padronizado": "AMBEV",
            "nome_emissor_fitch": "Ambev S.A. (antigo)",
            "nome_emissor_moodys": "",
            "nome_emissor_standard_and_poors": "",
            "cnpj_emissor": "12345678000199",
        },
    ])

    fitch = tmp_path / "fitch.csv"
    _escrever_csv(fitch, [{"no_entidade": "Ambev S.A.", "link": ""}])

    moodys = tmp_path / "moodys.csv"
    _escrever_csv(moodys, [{"no_entidade": "", "link": ""}])

    sp = tmp_path / "sp.csv"
    _escrever_csv(sp, [{"no_entidade": "", "link": ""}])

    consolidar(fitch, moodys, sp, output)

    with open(output, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["cnpj_emissor"] == "12345678000199"
    assert rows[0]["nome_emissor_fitch"] == "Ambev S.A."


def test_consolidar_ordem_alfabetica(tmp_path):
    fitch = tmp_path / "fitch.csv"
    _escrever_csv(fitch, [
        {"no_entidade": "Vale S.A.", "link": ""},
        {"no_entidade": "Ambev S.A.", "link": ""},
        {"no_entidade": "Banco Bradesco S.A.", "link": ""},
    ])

    moodys = tmp_path / "moodys.csv"
    _escrever_csv(moodys, [{"no_entidade": "", "link": ""}])

    sp = tmp_path / "sp.csv"
    _escrever_csv(sp, [{"no_entidade": "", "link": ""}])

    output = tmp_path / "out.csv"
    consolidar(fitch, moodys, sp, output)

    with open(output, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    padronizados = [r["nome_emissor_padronizado"] for r in rows]
    assert padronizados == sorted(padronizados)
    assert padronizados == ["AMBEV", "BANCO BRADESCO", "VALE"]


def test_consolidar_emissor_novo_adicionado(tmp_path):
    output = tmp_path / "out.csv"
    _escrever_csv(output, [
        {
            "nome_emissor_padronizado": "AMBEV",
            "nome_emissor_fitch": "Ambev S.A.",
            "nome_emissor_moodys": "",
            "nome_emissor_standard_and_poors": "",
            "cnpj_emissor": "",
        },
    ])

    fitch = tmp_path / "fitch.csv"
    _escrever_csv(fitch, [
        {"no_entidade": "Ambev S.A.", "link": ""},
        {"no_entidade": "Vale S.A.", "link": ""},
    ])

    moodys = tmp_path / "moodys.csv"
    _escrever_csv(moodys, [{"no_entidade": "", "link": ""}])

    sp = tmp_path / "sp.csv"
    _escrever_csv(sp, [{"no_entidade": "", "link": ""}])

    consolidar(fitch, moodys, sp, output)

    with open(output, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["nome_emissor_padronizado"] == "AMBEV"
    assert rows[1]["nome_emissor_padronizado"] == "VALE"


def test_consolidar_sem_nenhuma_fonte(tmp_path):
    moodys = tmp_path / "moodys.csv"
    _escrever_csv(moodys, [{"no_entidade": "", "link": ""}])

    sp = tmp_path / "sp.csv"
    _escrever_csv(sp, [{"no_entidade": "", "link": ""}])

    output = tmp_path / "out.csv"
    consolidar(tmp_path / "inexistente.csv", moodys, sp, output)

    with open(output, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows == []
