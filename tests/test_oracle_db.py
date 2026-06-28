import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from utils.oracle_db import (
    sanitizar_nome,
    inferir_tipo_oracle,
    parse_date_value,
    clean_row_value,
    obter_engine
)


def test_sanitizar_nome():
    # 1. Caixa alta
    assert sanitizar_nome("minha_coluna") == "MINHA_COLUNA"
    
    # 2. Acentos e caracteres especiais
    assert sanitizar_nome("Preço Unitário") == "PRECO_UNITARIO"
    assert sanitizar_nome("ação#referente&teste") == "ACAO_REFERENTE_TESTE"
    
    # 3. Múltiplos sublinhados consecutivos
    assert sanitizar_nome("coluna___teste") == "COLUNA_TESTE"
    assert sanitizar_nome("__coluna_teste__") == "COLUNA_TESTE"
    
    # 4. Prefixo C_ para dígitos no início
    assert sanitizar_nome("123coluna") == "C_123COLUNA"
    assert sanitizar_nome("2_data") == "C_2_DATA"
    
    # 5. Palavras reservadas do Oracle
    assert sanitizar_nome("DATE") == "DATE_VAL"
    assert sanitizar_nome("number") == "NUMBER_VAL"
    assert sanitizar_nome("table") == "TABLE_VAL"
    assert sanitizar_nome("select") == "SELECT_VAL"
    
    # 6. Limitação de tamanho (128 caracteres)
    long_name = "A" * 150
    assert len(sanitizar_nome(long_name)) == 128


def test_inferir_tipo_oracle():
    # 1. Booleano
    s_bool = pd.Series([True, False, None], dtype="boolean")
    assert inferir_tipo_oracle("is_active", s_bool) == "NUMBER(1)"
    
    # 2. Inteiro
    s_int = pd.Series([1, 2, 3], dtype="Int64")
    assert inferir_tipo_oracle("id", s_int) == "NUMBER(19)"
    
    # 3. Float / Numérico geral
    s_float = pd.Series([1.5, 2.3, None], dtype="float64")
    assert inferir_tipo_oracle("valor", s_float) == "NUMBER"
    
    # 4. Data / Datetime
    s_dt = pd.Series([datetime.now(), None])
    assert inferir_tipo_oracle("dt_captura", s_dt) == "DATE"
    
    # 5. String / Nome de coluna indicando data
    s_str_date = pd.Series(["2026-06-28", "2026-06-29"])
    assert inferir_tipo_oracle("data_referencia", s_str_date) == "DATE"
    assert inferir_tipo_oracle("anomes", s_str_date) == "DATE"
    
    # 6. String padrão
    s_str = pd.Series(["texto1", "texto2"])
    assert inferir_tipo_oracle("nome", s_str) == "VARCHAR2(4000)"


def test_parse_date_value():
    # 1. Objetos datetime e date passados diretamente
    dt = datetime(2026, 6, 28, 12, 0, 0)
    d = date(2026, 6, 28)
    assert parse_date_value(dt) == dt
    assert parse_date_value(d) == d
    
    # 2. Strings em formatos válidos
    assert parse_date_value("2026-06-28 12:00:00") == datetime(2026, 6, 28, 12, 0, 0)
    assert parse_date_value("2026-06-28") == datetime(2026, 6, 28, 0, 0, 0)
    assert parse_date_value("28/06/2026") == datetime(2026, 6, 28, 0, 0, 0)
    assert parse_date_value("28/06/2026 12:00:00") == datetime(2026, 6, 28, 12, 0, 0)
    
    # 3. Casos nulos / inválidos
    assert parse_date_value(None) is None
    assert parse_date_value("") is None
    assert parse_date_value("NAT") is None
    assert parse_date_value("NAN") is None
    assert parse_date_value("texto_aleatorio") is None


def test_clean_row_value():
    # 1. Nulos e pandas.NA/NaT
    assert clean_row_value(None, "VARCHAR2") is None
    assert clean_row_value(pd.NA, "VARCHAR2") is None
    assert clean_row_value(pd.NaT, "DATE") is None
    
    # 2. Floats inválidos (NaN, inf)
    assert clean_row_value(float("nan"), "NUMBER") is None
    assert clean_row_value(float("inf"), "NUMBER") is None
    assert clean_row_value(float("-inf"), "NUMBER") is None
    assert clean_row_value(1.23, "NUMBER") == 1.23
    
    # 3. String vazia -> None
    assert clean_row_value("", "VARCHAR2") is None
    
    # 4. Data
    assert clean_row_value("2026-06-28", "DATE") == datetime(2026, 6, 28, 0, 0, 0)


def test_obter_engine_bypass():
    # Testa bypass caso variáveis de ambiente não estejam configuradas
    orig_user = os.environ.get("ORACLE_DB_USER")
    if "ORACLE_DB_USER" in os.environ:
        del os.environ["ORACLE_DB_USER"]
        
    try:
        assert obter_engine() is None
    finally:
        if orig_user is not None:
            os.environ["ORACLE_DB_USER"] = orig_user
