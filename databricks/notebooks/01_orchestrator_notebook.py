# Databricks notebook source
# MAGIC %md
# MAGIC # Pulse Ratings Brasil — Orquestrador Interativo
# MAGIC
# MAGIC Este notebook permite a execução interativa, homologação e depuração dos scrapers de ratings e dos pipelines de consolidação do **Pulse Ratings Brasil** dentro do ambiente Databricks.
# MAGIC
# MAGIC ### Funcionalidades:
# MAGIC - Executar o pipeline completo ou filtrar por grupo de scrapers (`ratings`, `emissores`) ou scraper específico.
# MAGIC - Configurar execução paralela ou sequencial com controle de threads simultâneas.
# MAGIC - Carregar segredos de um Databricks Secret Scope (`pulse_ratings`) ou variáveis de ambiente.
# MAGIC - Exportar automaticamente os dados consolidados para tabelas Delta Lake no Hive Metastore ou Unity Catalog.

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Instalação de Dependências
# MAGIC Instala as bibliotecas necessárias para o projeto a partir do arquivo `requirements.txt`.

# COMMAND ----------
# MAGIC %pip install -r ../requirements.txt

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Configuração de Parâmetros de Execução (Widgets)
# MAGIC Ajuste os valores abaixo diretamente na barra superior de widgets para controlar o comportamento da execução manual.

# COMMAND ----------
# Definição e limpeza dos widgets do Databricks
try:
    dbutils.widgets.dropdown("mode", "full_pipeline", ["full_pipeline", "by_group", "single_scraper", "catalog_only"], "1. Modo de Execução")
    dbutils.widgets.dropdown("group", "ratings", ["ratings", "emissores", "misc"], "2. Grupo (se Modo = by_group)")
    dbutils.widgets.combobox("scraper", "fitch_ratings", [
        "fitch_ratings", "fitch_emissores",
        "moodys_ratings", "moodys_emissores",
        "standard_and_poors_ratings", "standard_and_poors_emissores",
        "austin_ratings", "austin_emissores",
        "liberum_ratings", "liberum_emissores"
    ], "3. Scraper Específico")
    dbutils.widgets.dropdown("parallel", "true", ["true", "false"], "4. Execução Paralela")
    dbutils.widgets.text("max_workers", "4", "5. Max Workers")
    dbutils.widgets.dropdown("skip_db", "true", ["true", "false"], "6. Pular Banco Oracle")
    dbutils.widgets.text("secret_scope", "pulse_ratings", "7. Secret Scope Databricks")
    dbutils.widgets.dropdown("export_delta", "false", ["false", "true"], "8. Exportar para Delta Lake")
    dbutils.widgets.text("delta_catalog", "hive_metastore", "9. Catálogo Delta Lake")
    dbutils.widgets.text("delta_schema", "pulse_ratings", "10. Schema Delta Lake")
except Exception as e:
    print(f"Aviso ao inicializar widgets: {e}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Inicialização e Execução do Pipeline
# MAGIC Localiza a raiz do repositório clonado no Databricks Git Folders, ajusta o `sys.path`, carrega os segredos e invoca o orquestrador principal.

# COMMAND ----------
import os
import sys
import time
from pathlib import Path

# Ajusta sys.path para a raiz do repositório clonado
NOTEBOOK_DIR = Path.cwd().resolve()
REPO_ROOT = NOTEBOOK_DIR.parent.parent if NOTEBOOK_DIR.name == "notebooks" else NOTEBOOK_DIR
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

print(f"Repositório ativo: {REPO_ROOT}")

# Leitura dos widgets
mode = dbutils.widgets.get("mode")
group_val = dbutils.widgets.get("group") if mode == "by_group" else None
scraper_val = dbutils.widgets.get("scraper").strip() if mode == "single_scraper" else None
parallel_val = dbutils.widgets.get("parallel").lower() == "true"
max_workers_val = int(dbutils.widgets.get("max_workers") or "4")
skip_db_val = dbutils.widgets.get("skip_db").lower() == "true"
secret_scope = dbutils.widgets.get("secret_scope").strip() or "pulse_ratings"
export_delta_val = dbutils.widgets.get("export_delta").lower() == "true"
delta_catalog = dbutils.widgets.get("delta_catalog").strip() or "hive_metastore"
delta_schema = dbutils.widgets.get("delta_schema").strip() or "pulse_ratings"

print("--- Configuração da Execução ---")
print(f"Modo: {mode}")
if group_val:
    print(f"Grupo selecionado: {group_val}")
if scraper_val:
    print(f"Scraper selecionado: {scraper_val}")
print(f"Paralelo: {parallel_val} (max_workers={max_workers_val})")
print(f"Skip Oracle DB: {skip_db_val}")
print(f"Export Delta: {export_delta_val} ({delta_catalog}.{delta_schema})")
print("--------------------------------")

# Carregamento de segredos via Secret Scope / os.environ
from databricks.run_pulse_ratings_brasil_job import load_secrets
loaded_secrets = load_secrets(scope=secret_scope)
if loaded_secrets:
    print(f"Segredos configurados ({len(loaded_secrets)}): {', '.join(loaded_secrets.keys())}")

if skip_db_val:
    os.environ["SKIP_ORACLE_DB"] = "1"

from utils.paths import get_data_dir
data_dir = get_data_dir()
data_dir.mkdir(parents=True, exist_ok=True)
print(f"Diretório de dados ativo: {data_dir}")

# Execução conforme o modo selecionado
import run_all

start_exec = time.time()

if mode == "catalog_only":
    from scripts.generate_catalog import generate
    generate()
    print("✔ Catálogo de datasets gerado com sucesso.")
else:
    run_all.main(
        group=group_val,
        scraper=scraper_val,
        parallel=parallel_val,
        max_workers=max_workers_val,
    )
    # Se foi full pipeline, executa geração de JSON de consulta
    if mode == "full_pipeline":
        try:
            from scripts.gerar_consulta_json import main as gerar_consulta
            gerar_consulta()
            print("✔ JSON consolidado de consulta gerado com sucesso.")
        except Exception as e:
            print(f"Aviso ao gerar JSON de consulta: {e}")

elapsed_exec = time.time() - start_exec
print()
print(f"✔ Execução do pipeline finalizada em {elapsed_exec:.1f}s.")

# Exportação opcional para Delta Lake
if export_delta_val:
    print(f"\nExportando dados para tabelas Delta Lake ({delta_catalog}.{delta_schema})...")
    from databricks.delta_exporter import export_csv_to_delta
    summary = export_csv_to_delta(
        catalog_name=delta_catalog,
        schema_name=delta_schema,
        data_dir=data_dir,
        write_mode="overwrite",
    )
    print(f"✔ Exportação para Delta Lake concluída: {summary.get('total_files', 0)} arquivos.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. Resumo e Inspeção dos Arquivos Gerados

# COMMAND ----------
import pandas as pd
from datetime import datetime

files_info = []
for p in sorted(data_dir.glob("*.csv")):
    stat = p.stat()
    files_info.append({
        "Arquivo": p.name,
        "Tamanho (KB)": round(stat.st_size / 1024, 2),
        "Última Modificação": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
    })

summary_df = pd.DataFrame(files_info)
print(f"Total de arquivos CSV em {data_dir}: {len(files_info)}")
try:
    display(summary_df)
except Exception:
    print(summary_df.to_string(index=False))
