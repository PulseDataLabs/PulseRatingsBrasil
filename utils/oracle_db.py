"""
utils/oracle_db.py
------------------
Módulo utilitário para gerenciamento de conexão e persistência no banco de dados Oracle Cloud Autonomous Database.
"""

import logging
import os
import re
import unicodedata
import urllib.parse
from datetime import date, datetime

import numpy as np
import pandas as pd
import sqlalchemy
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

logger = logging.getLogger("utils.oracle_db")

# Garante o Thin Mode do oracledb explicitamente
try:
    import oracledb

    oracledb.init_oracle_client = None
except Exception as e:
    logger.debug(f"Erro ao tentar configurar oracledb.init_oracle_client = None: {e}")


def sanitizar_nome(nome: str) -> str:
    """
    Sanitiza um nome de coluna ou tabela para os padrões do Oracle.
    - Converte para maiúsculas.
    - Remove acentos e caracteres especiais.
    - Substitui espaços e delimitadores por sublinhado (_).
    - Adiciona prefixo 'C_' se iniciar com dígito.
    - Adiciona sufixo '_VAL' para palavras reservadas do Oracle.
    - Limita o tamanho a 128 caracteres.
    """
    if not nome:
        return ""

    # 1. Normalizar e remover acentos
    n = unicodedata.normalize("NFKD", nome)
    n = n.encode("ascii", "ignore").decode("ascii")

    # 2. Caixa alta e substituição de caracteres não-alfanuméricos
    n = n.upper()
    n = re.sub(r"[^A-Z0-9_]", "_", n)

    # 3. Limpeza de múltiplos sublinhados consecutivos e das bordas
    n = re.sub(r"_+", "_", n)
    n = n.strip("_")

    # 4. Se começar com dígito, adiciona o prefixo C_
    if n and n[0].isdigit():
        n = "C_" + n

    # 5. Palavras reservadas do Oracle
    palavras_reservadas = {
        "ACCESS",
        "ADD",
        "ALL",
        "ALTER",
        "AND",
        "ANY",
        "AS",
        "ASC",
        "AUDIT",
        "BETWEEN",
        "BY",
        "CHAR",
        "CHECK",
        "CLUSTER",
        "COLUMN",
        "COMMENT",
        "COMPRESS",
        "CONNECT",
        "CREATE",
        "CURRENT",
        "DATE",
        "DECIMAL",
        "DEFAULT",
        "DELETE",
        "DESC",
        "DISTINCT",
        "DROP",
        "ELSE",
        "EXCLUSIVE",
        "EXISTS",
        "FILE",
        "FLOAT",
        "FOR",
        "FROM",
        "GRANT",
        "GROUP",
        "HAVING",
        "IDENTIFIED",
        "IMMEDIATE",
        "IN",
        "INCREMENT",
        "INDEX",
        "INITIAL",
        "INSERT",
        "INTEGER",
        "INTERSECT",
        "INTO",
        "IS",
        "LEVEL",
        "LIKE",
        "LOCK",
        "LONG",
        "MAXEXTENTS",
        "MINUS",
        "MLSLABEL",
        "MODE",
        "MODIFY",
        "NOAUDIT",
        "NOCOMPRESS",
        "NOT",
        "NOWAIT",
        "NULL",
        "NUMBER",
        "OF",
        "OFFLINE",
        "ON",
        "ONLINE",
        "OPTION",
        "OR",
        "ORDER",
        "PCTFREE",
        "PRIOR",
        "PRIVILEGES",
        "PUBLIC",
        "RAW",
        "RENAME",
        "RESOURCE",
        "REVOKE",
        "ROW",
        "ROWID",
        "ROWNUM",
        "ROWS",
        "SELECT",
        "SESSION",
        "SET",
        "SHARE",
        "SIZE",
        "SMALLINT",
        "START",
        "SUCCESSFUL",
        "SYNONYM",
        "SYSDATE",
        "TABLE",
        "THEN",
        "TO",
        "TRIGGER",
        "UID",
        "UNION",
        "UNIQUE",
        "UPDATE",
        "USER",
        "VALIDATE",
        "VALUES",
        "VARCHAR",
        "VARCHAR2",
        "VIEW",
        "WHENEVER",
        "WHERE",
        "WITH",
    }

    if n in palavras_reservadas:
        n = n + "_VAL"

    # 6. Limita a 128 caracteres
    return n[:128]


def inferir_tipo_oracle(col_name: str, series: pd.Series) -> str:
    """
    Infece o tipo de dado do Oracle com base em uma Series do Pandas.
    - Boolean -> NUMBER(1) (deve vir primeiro!)
    - Integer -> NUMBER(19)
    - Float/Numeric -> NUMBER
    - Datetime -> DATE
    - String/Outros -> VARCHAR2(4000)
    """
    # 1. Booleano
    if pd.api.types.is_bool_dtype(series):
        return "NUMBER(1)"

    # 2. Inteiro
    if pd.api.types.is_integer_dtype(series):
        return "NUMBER(19)"

    # 3. Float / Numérico Geral
    if pd.api.types.is_numeric_dtype(series):
        return "NUMBER"

    # 4. Data / Datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "DATE"

    # Tratamento heurístico para colunas de data em formato string
    col_name_lower = col_name.lower()
    candidatos_data = [
        "data",
        "date",
        "dt_",
        "_dt",
        "periodo",
        "anomes",
        "ano_mes",
        "data_base",
        "data_referencia",
        "data_captura",
    ]
    if any(cand in col_name_lower for cand in candidatos_data):
        return "DATE"

    # 5. String
    return "VARCHAR2(4000)"


def parse_date_value(val) -> datetime | date | None:
    """
    Converte um valor genérico em um objeto datetime/date compatível com o Oracle.
    """
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (datetime, date)):
        return val

    val_str = str(val).strip()
    if not val_str or val_str.upper() in ["NAN", "NAT", "NONE"]:
        return None

    # Formatos de data suportados
    formatos = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%Y/%m/%d",
    )
    for fmt in formatos:
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            continue

    # Fallback via pandas to_datetime
    try:
        dt = pd.to_datetime(val_str)
        if pd.isna(dt):
            return None
        return dt.to_pydatetime()
    except Exception:
        return None


def clean_row_value(val, col_type: str):
    """
    Trata valores especiais do numpy/pandas (NaN, NaT, inf) para None,
    e formata adequadamente datas para inserção segura no Oracle.
    """
    if val is None or pd.isna(val):
        return None

    # Trata valores de ponto flutuante inválidos
    if isinstance(val, (float, np.floating)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)

    # Converte strings vazias para None
    if val == "":
        return None

    # Trata tipo DATE
    if col_type == "DATE":
        return parse_date_value(val)

    return val


def obter_engine() -> sqlalchemy.engine.Engine | None:
    """
    Gera o engine de conexão SQLAlchemy para o Oracle Autonomous Database.
    Garante o uso de Thin Mode e pre-ping, configurando mTLS se a carteira (wallet) estiver configurada.
    """
    user = os.environ.get("ORACLE_DB_USER")
    password = os.environ.get("ORACLE_DB_PASSWORD")
    dsn = os.environ.get("ORACLE_DB_DSN")
    wallet_dir = os.environ.get("ORACLE_DB_WALLET_DIR")
    wallet_password = os.environ.get("ORACLE_DB_WALLET_PASSWORD")

    if not user or not password or not dsn:
        logger.debug("Credenciais do banco de dados Oracle não configuradas completamente.")
        return None

    # Trata a senha para caracteres especiais que quebram a URL de conexão
    safe_password = urllib.parse.quote_plus(password)

    # URL de conexão com dialeto oracle+oracledb
    connection_url = f"oracle+oracledb://{user}:{safe_password}@{dsn}"

    connect_args = {}

    # Se a pasta wallet for especificada e não vazia, ativa Mutual TLS (mTLS)
    if wallet_dir and os.path.exists(wallet_dir):
        try:
            files = os.listdir(wallet_dir)
            if files:
                connect_args["config_dir"] = wallet_dir
                connect_args["wallet_location"] = wallet_dir
                if wallet_password:
                    connect_args["wallet_password"] = wallet_password
                logger.info(f"Conexão configurada em modo Mutual TLS (mTLS) usando wallet: {wallet_dir}")
        except Exception as e:
            logger.warning(f"Erro ao ler diretório da wallet {wallet_dir}: {e}. Tentando One-Way TLS.")

    if not connect_args:
        logger.info("Conexão configurada em modo One-Way TLS.")

    engine = sqlalchemy.create_engine(connection_url, connect_args=connect_args, pool_pre_ping=True)
    return engine


def persistir_no_oracle(arquivo_path, registros: list[dict], todas: list[dict], cabecalho: list[str]) -> None:
    """
    Persiste os dados no Oracle Autonomous Database de forma automatizada e resiliente.
    """
    # Bypass / Dry-run Check
    if os.environ.get("SKIP_ORACLE_DB") == "1":
        logger.info("SKIP_ORACLE_DB ativo. Ignorando persistência no Oracle.")
        return

    engine = obter_engine()
    if not engine:
        logger.debug("Ignorando persistência no Oracle (credenciais ausentes).")
        return

    # Nome da tabela a partir do nome do arquivo
    nome_arquivo = os.path.basename(arquivo_path)
    nome_sem_extensao = os.path.splitext(nome_arquivo)[0]
    table_name = sanitizar_nome(nome_sem_extensao)

    # Cria os DataFrames
    df_novos = pd.DataFrame(registros)
    df_final = pd.DataFrame(todas)

    # Alinha as colunas dos DataFrames com a ordem do cabeçalho original
    for col in cabecalho:
        if col not in df_novos.columns:
            df_novos[col] = None
        if col not in df_final.columns:
            df_final[col] = None

    df_novos = df_novos[cabecalho]
    df_final = df_final[cabecalho]

    # Infece os tipos das colunas
    inferred_types = {col: inferir_tipo_oracle(col, df_final[col]) for col in cabecalho}

    # Sanitiza as colunas da tabela
    sanitised_columns = [sanitizar_nome(col) for col in cabecalho]

    # Verifica se a tabela já existe no banco
    inspector = sqlalchemy.inspect(engine)
    table_exists = inspector.has_table(table_name) or inspector.has_table(table_name.upper())

    # Auto-criação da tabela caso ela não exista
    if not table_exists:
        logger.info(f"Tabela {table_name} não encontrada no banco. Criando tabela...")
        columns_ddl = [
            f"{san_col} {inferred_types[orig_col]}" for san_col, orig_col in zip(sanitised_columns, cabecalho)
        ]
        create_ddl = f"CREATE TABLE {table_name} ({', '.join(columns_ddl)})"
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text(create_ddl))
        logger.info(f"Tabela {table_name} criada com sucesso.")

        # Como a tabela acabou de ser criada, faremos a carga completa inicial (df_final)
        executar_carga(engine, table_name, df_final, sanitised_columns, inferred_types, truncate=False)
        return

    # Identifica se a tabela possui alguma coluna de período ou data
    colunas_data_candidatas = [
        "anomes",
        "ano_mes",
        "data_base",
        "data_referencia",
        "data_captura",
        "data",
        "dt_captura",
        "dt_referencia",
        "periodo",
    ]
    date_col = None
    for col in cabecalho:
        if col.lower() in colunas_data_candidatas:
            date_col = col
            break

    if date_col:
        # Modo Incremental: deleta os períodos existentes no lote novo antes de inserir
        unique_periods = df_novos[date_col].dropna().unique()
        san_date_col = sanitizar_nome(date_col)

        logger.info(
            f"Tabela {table_name} possui coluna de data ({date_col}). Executando deleção de {len(unique_periods)} períodos específicos antes da inserção incremental."
        )

        with engine.begin() as conn:
            for period in unique_periods:
                cleaned_period = clean_row_value(period, inferred_types[date_col])
                if cleaned_period is None:
                    conn.execute(sqlalchemy.text(f"DELETE FROM {table_name} WHERE {san_date_col} IS NULL"))
                else:
                    conn.execute(
                        sqlalchemy.text(f"DELETE FROM {table_name} WHERE {san_date_col} = :val"),
                        {"val": cleaned_period},
                    )

        # Insere apenas o novo lote
        executar_carga(engine, table_name, df_novos, sanitised_columns, inferred_types, truncate=False)
    else:
        # Modo Full: limpa a tabela (TRUNCATE) e insere o DataFrame final inteiro
        logger.info(
            f"Tabela {table_name} não possui colunas de data/período. Executando TRUNCATE TABLE e carga completa."
        )
        executar_carga(engine, table_name, df_final, sanitised_columns, inferred_types, truncate=True)


def executar_carga(
    engine: sqlalchemy.engine.Engine,
    table_name: str,
    df: pd.DataFrame,
    sanitised_columns: list[str],
    inferred_types: dict[str, str],
    truncate: bool = False,
) -> None:
    """
    Executa a carga em lotes utilizando cursor.executemany bruto para alta performance.
    """
    # Limpa a tabela se solicitado
    if truncate:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text(f"TRUNCATE TABLE {table_name}"))

    # Prepara a query de inserção (usa posicional binding do Oracle ':1', ':2', etc.)
    placeholders = [f":{i + 1}" for i in range(len(sanitised_columns))]
    insert_sql = (
        f"INSERT INTO {table_name} ({', '.join(sanitised_columns)}) VALUES ({', '.join(placeholders)})"
    )

    # Limpa e formata todas as linhas para inserção
    cleaned_rows = []
    for _, row in df.iterrows():
        row_values = [clean_row_value(row[col], inferred_types[col]) for col in df.columns]
        cleaned_rows.append(tuple(row_values))

    chunk_size = 5000
    total_loaded = 0

    with engine.begin() as conn:
        raw_conn = getattr(conn, "driver_connection", None) or conn.connection
        with raw_conn.cursor() as cursor:
            for i in range(0, len(cleaned_rows), chunk_size):
                chunk = cleaned_rows[i : i + chunk_size]
                cursor.executemany(insert_sql, chunk)
                total_loaded += len(chunk)

    logger.info(f"Carga concluída para {table_name} → {total_loaded} linhas carregadas via executemany.")
