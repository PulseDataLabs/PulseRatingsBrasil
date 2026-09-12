# Databricks notebook source
# MAGIC %md
# MAGIC # Pulse Ratings Brasil — Exportador Delta Lake
# MAGIC
# MAGIC Este notebook lê os arquivos CSV gerados pelo pipeline do **Pulse Ratings Brasil** e grava/atualiza tabelas **Delta Lake** no **Hive Metastore** ou no **Unity Catalog**.
# MAGIC
# MAGIC ### Recursos:
# MAGIC - Adiciona colunas de auditoria automática: `_ingestion_timestamp` e `_source_file`.
# MAGIC - Sanitiza nomes de colunas com caracteres especiais para compatibilidade total com o motor Delta Lake.
# MAGIC - Suporta tanto criação de banco no Hive Metastore clássico (`pulse_ratings.<tabela>`) quanto no Unity Catalog (`<catalogo>.<schema>.<tabela>`).
# MAGIC - Permite execução agendada como segunda etapa (Task 2) de um Databricks Workflow ou execução avulsa manual.

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Configuração de Parâmetros (Widgets)

# COMMAND ----------
try:
    dbutils.widgets.text("catalog_name", "hive_metastore", "1. Catálogo (Unity Catalog ou hive_metastore)")
    dbutils.widgets.text("schema_name", "pulse_ratings", "2. Schema / Database")
    dbutils.widgets.text("data_dir", "", "3. Diretório de Dados (vazio = auto-detect)")
    dbutils.widgets.dropdown("write_mode", "overwrite", ["overwrite", "append"], "4. Modo de Gravação")
    dbutils.widgets.text("table_filter", "", "5. Filtro de Tabelas (separadas por vírgula ou vazio)")
except Exception as e:
    print(f"Aviso ao inicializar widgets: {e}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Execução da Exportação para Delta Lake

# COMMAND ----------
import os
import sys
from pathlib import Path
import pandas as pd

# Ajusta sys.path para a raiz do repositório clonado
NOTEBOOK_DIR = Path.cwd().resolve()
REPO_ROOT = NOTEBOOK_DIR.parent.parent if NOTEBOOK_DIR.name == "notebooks" else NOTEBOOK_DIR
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

# Leitura dos widgets
catalog_name = dbutils.widgets.get("catalog_name").strip() or "hive_metastore"
schema_name = dbutils.widgets.get("schema_name").strip() or "pulse_ratings"
data_dir_param = dbutils.widgets.get("data_dir").strip()
write_mode = dbutils.widgets.get("write_mode")
table_filter_raw = dbutils.widgets.get("table_filter").strip()
table_filter = [t.strip().lower() for t in table_filter_raw.split(",") if t.strip()] if table_filter_raw else None

# Resolução do diretório de dados
if data_dir_param:
    target_data_dir = Path(data_dir_param)
else:
    from utils.paths import get_data_dir
    target_data_dir = get_data_dir()

print("--- Parâmetros do Exportador Delta ---")
print(f"Catálogo: {catalog_name}")
print(f"Schema: {schema_name}")
print(f"Diretório de dados: {target_data_dir}")
print(f"Modo de gravação: {write_mode}")
if table_filter:
    print(f"Tabelas filtradas: {table_filter}")
print("--------------------------------------")

# Importa o utilitário de exportação
from databricks.delta_exporter import export_csv_to_delta

res = export_csv_to_delta(
    catalog_name=catalog_name,
    schema_name=schema_name,
    data_dir=target_data_dir,
    write_mode=write_mode,
    table_filter=table_filter,
    spark=spark,
)

print()
print(f"✔ Processamento finalizado! {res.get('total_files', 0)} arquivos inspecionados.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Resumo das Tabelas Delta Criadas / Atualizadas

# COMMAND ----------
tables_data = []
for tbl_name, info in res.get("tables", {}).items():
    tables_data.append({
        "Tabela": tbl_name,
        "Nome Completo": info.get("full_table_name"),
        "Status": info.get("status"),
        "Linhas": info.get("rows", 0),
        "Colunas": info.get("columns", 0),
        "Arquivo de Origem": info.get("source_file"),
        "Erro": info.get("error", "")
    })

summary_df = pd.DataFrame(tables_data)
try:
    display(summary_df)
except Exception:
    print(summary_df.to_string(index=False))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. Consultas Rápidas de Exemplo (Databricks SQL)
# MAGIC Exemplos de consultas analíticas sobre as tabelas Delta consolidadas.

# COMMAND ----------
# MAGIC %sql
# MAGIC -- Exemplo: Amostra das emissões consolidadas com ratings
# MAGIC SELECT 
# MAGIC   no_emissor_padronizado,
# MAGIC   cnpj_emissor,
# MAGIC   de_rating_br,
# MAGIC   de_outlook,
# MAGIC   dt_acao_rating,
# MAGIC   agencia,
# MAGIC   _ingestion_timestamp
# MAGIC FROM pulse_ratings.ratings_emissoes
# MAGIC LIMIT 10;
