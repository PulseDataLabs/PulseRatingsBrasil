"""
Pulse Ratings Brasil – Utilitário de Exportação para Delta Lake
Compatível com Unity Catalog e Hive Metastore no Databricks.
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("delta_exporter")


def sanitize_column_name(col_name: str) -> str:
    """
    Sanitiza o nome de coluna para conformidade com o formato Delta Lake.
    Substitui espaços e caracteres especiais não permitidos por underline.
    """
    # Caracteres proibidos ou problemáticos no Delta Lake
    cleaned = re.sub(r"[ ,;{}()=\n\t\-\./\\]+", "_", col_name.strip()).strip("_")
    if cleaned and cleaned[0].isdigit():
        cleaned = f"col_{cleaned}"
    return cleaned or "col_unnamed"


def get_spark_session():
    """Obtém a SparkSession ativa no Databricks ou cria uma nova se disponível."""
    try:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    except Exception as e:
        logger.warning(f"SparkSession não disponível: {e}")
        return None


def export_csv_to_delta(
    catalog_name: str = "hive_metastore",
    schema_name: str = "pulse_ratings",
    data_dir: Path | str | None = None,
    write_mode: str = "overwrite",
    table_filter: list[str] | None = None,
    spark: Any = None,
) -> dict[str, Any]:
    """
    Lê arquivos CSV do diretório de dados e grava/atualiza tabelas Delta Lake.
    Adiciona colunas de auditoria (_ingestion_timestamp e _source_file).
    Retorna um dicionário com o resumo das tabelas exportadas.
    """
    if spark is None:
        spark = get_spark_session()

    if spark is None:
        raise RuntimeError("SparkSession não pôde ser inicializada no ambiente atual.")

    from pyspark.sql.functions import current_timestamp, lit

    # Habilita evolução de schema e mapeamento de colunas no Delta
    try:
        spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
    except Exception:
        pass

    if data_dir is None:
        from utils.paths import get_data_dir
        data_dir = get_data_dir()
    else:
        data_dir = Path(data_dir)

    if not data_dir.exists():
        raise FileNotFoundError(f"Diretório de dados não encontrado: {data_dir}")

    # Cria catalog/schema se necessário
    is_hive_metastore = (
        not catalog_name or catalog_name.lower() in ("hive_metastore", "default")
    )
    if is_hive_metastore:
        spark.sql(f"CREATE DATABASE IF NOT EXISTS {schema_name}")
    else:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}")

    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        logger.warning(f"Nenhum arquivo CSV encontrado em {data_dir}")
        return {"total_files": 0, "tables": {}}

    results: dict[str, dict[str, Any]] = {}

    for csv_path in csv_files:
        table_name = csv_path.stem.lower().replace("-", "_")

        # Filtro opcional por tabela
        if table_filter and table_name not in table_filter and csv_path.name not in table_filter:
            continue

        full_table = (
            f"{schema_name}.{table_name}"
            if is_hive_metastore
            else f"{catalog_name}.{schema_name}.{table_name}"
        )

        logger.info(f"Exportando CSV para Delta: {csv_path.name} -> {full_table}")

        try:
            spark_read_path = str(csv_path)
            if spark_read_path.startswith("/Workspace"):
                spark_read_path = f"file:{spark_read_path}"

            try:
                df = (
                    spark.read
                    .option("header", "true")
                    .option("inferSchema", "true")
                    .option("multiLine", "true")
                    .option("escape", '"')
                    .csv(spark_read_path)
                )
                if not df.columns:
                    raise ValueError("0 colunas encontradas no arquivo.")
            except Exception as spark_err:
                logger.debug(f"Fallback pandas para {csv_path.name}: {spark_err}")
                import pandas as pd
                pdf = pd.read_csv(csv_path, dtype=str).fillna("")
                df = spark.createDataFrame(pdf)

            # Sanitiza nomes de colunas
            for col in df.columns:
                sanitized = sanitize_column_name(col)
                if sanitized != col:
                    df = df.withColumnRenamed(col, sanitized)

            # Adiciona colunas de auditoria
            df = df.withColumn("_ingestion_timestamp", current_timestamp()) \
                   .withColumn("_source_file", lit(csv_path.name))

            # Grava na tabela Delta
            writer = df.write.format("delta").mode(write_mode)
            if write_mode == "overwrite":
                writer = writer.option("overwriteSchema", "true")

            writer.saveAsTable(full_table)

            row_count = df.count()
            col_count = len(df.columns)
            results[table_name] = {
                "status": "success",
                "full_table_name": full_table,
                "rows": row_count,
                "columns": col_count,
                "source_file": csv_path.name,
            }
            logger.info(f"✔ Tabela Delta '{full_table}' atualizada: {row_count} linhas.")

        except Exception as e:
            logger.error(f"✖ Erro ao exportar '{csv_path.name}': {e}", exc_info=True)
            results[table_name] = {
                "status": "error",
                "full_table_name": full_table,
                "error": str(e),
                "source_file": csv_path.name,
            }

    return {"total_files": len(csv_files), "tables": results}
