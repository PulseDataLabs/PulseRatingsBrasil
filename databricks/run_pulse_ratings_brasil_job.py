#!/usr/bin/env python3
"""
Pulse Ratings Brasil – Databricks Workflows Python Script Entrypoint
Executa o pipeline completo ou modular no Databricks Git Folders (Repos)
como uma tarefa agendada (Workflows / Jobs) ou via script interativo.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# ── 1. Ajuste dinâmico de sys.path e diretório de trabalho ─────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

from dotenv import load_dotenv

# Carrega .env se existir na raiz do repositório
load_dotenv(REPO_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("databricks_job")


# ── 2. Carregamento de segredos (Secret Scope com fallback de os.environ) ──
def get_dbutils():
    """Tenta obter a instância de dbutils do Databricks de forma segura."""
    try:
        from databricks.sdk.runtime import dbutils
        return dbutils
    except Exception:
        pass
    try:
        from pyspark.sql import SparkSession
        from pyspark.dbutils import DBUtils
        spark = SparkSession.builder.getOrCreate()
        return DBUtils(spark)
    except Exception:
        return None


def load_secrets(scope: str = "pulse_ratings") -> dict[str, str]:
    """
    Carrega segredos do Databricks Secret Scope informado.
    Caso o scope não exista ou uma chave não seja encontrada, mantém
    o valor já configurado nas variáveis de ambiente (os.environ).
    """
    keys_to_load = [
        "SP_GLOBAL_API_KEY",
        "CNPJABERTO_API_KEY",
        "SEARXNG_URL",
        "BRAVE_SEARCH_API_KEY",
        "BING_SEARCH_API_KEY",
        "DATABRICKS_DATA_PATH",
        "DATA_DIR",
        "ORACLE_DB_USER",
        "ORACLE_DB_PASSWORD",
        "ORACLE_DB_DSN",
        "ORACLE_DB_WALLET_DIR",
        "ORACLE_DB_WALLET_PASSWORD",
        "ORACLE_DB_WALLET_BASE64",
        "SKIP_ORACLE_DB",
    ]

    dbutils = get_dbutils()
    loaded_summary = {}

    for key in keys_to_load:
        val = None
        if dbutils:
            try:
                val = dbutils.secrets.get(scope=scope, key=key)
            except Exception:
                pass

        if not val:
            val = os.environ.get(key)

        if val is not None and str(val).strip():
            str_val = str(val).strip()
            os.environ[key] = str_val
            is_sensitive = any(
                sens in key.upper()
                for sens in ["KEY", "PASSWORD", "SECRET", "BASE64"]
            )
            loaded_summary[key] = "***" if is_sensitive else str_val

    # Se ORACLE_DB_WALLET_BASE64 foi fornecido e não há diretório de wallet definido
    wallet_b64 = os.environ.get("ORACLE_DB_WALLET_BASE64")
    if wallet_b64 and not os.environ.get("ORACLE_DB_WALLET_DIR"):
        try:
            import base64
            import io
            import zipfile

            wallet_dir = Path("/tmp/oracle_wallet")
            wallet_dir.mkdir(parents=True, exist_ok=True)
            raw = base64.b64decode(wallet_b64)
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                z.extractall(wallet_dir)
            os.environ["ORACLE_DB_WALLET_DIR"] = str(wallet_dir)
            logger.info("Oracle Wallet descompactada com sucesso em /tmp/oracle_wallet")
        except Exception as e:
            logger.warning(f"Não foi possível descompactar ORACLE_DB_WALLET_BASE64: {e}")

    return loaded_summary


# ── 3. Delegação para o orquestrador principal ─────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Pulse Ratings Brasil – Databricks Workflow Job Entrypoint"
    )
    parser.add_argument(
        "--group",
        type=str,
        default=None,
        help="Executa apenas os scrapers de um grupo específico (ex: ratings, emissores)",
    )
    parser.add_argument(
        "--scraper",
        type=str,
        default=None,
        help="Executa apenas um scraper específico (ex: fitch_ratings)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Executa scrapers em paralelo usando threads (padrão: True)",
    )
    parser.add_argument(
        "--sequential",
        action="store_false",
        dest="parallel",
        help="Executa scrapers sequencialmente",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Número máximo de threads simultâneas (padrão: 4)",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Ignora a gravação e persistência no banco de dados Oracle",
    )
    parser.add_argument(
        "--generate-catalog",
        action="store_true",
        help="Gera e atualiza apenas o arquivo data/datasets.json a partir dos scrapers",
    )
    parser.add_argument(
        "--secret-scope",
        type=str,
        default="pulse_ratings",
        help="Nome do Databricks Secret Scope para leitura de credenciais (padrão: pulse_ratings)",
    )
    parser.add_argument(
        "--export-delta",
        action="store_true",
        help="Exporta automaticamente os dados em CSV para tabelas Delta Lake após a execução",
    )
    parser.add_argument(
        "--delta-catalog",
        type=str,
        default="hive_metastore",
        help="Nome do catálogo para tabelas Delta (padrão: hive_metastore)",
    )
    parser.add_argument(
        "--delta-schema",
        type=str,
        default="pulse_ratings",
        help="Nome do schema/database para tabelas Delta (padrão: pulse_ratings)",
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("▶ Iniciando Pulse Ratings Brasil Databricks Job")
    logger.info(f"  Repositório: {REPO_ROOT}")
    logger.info(f"  Modo paralelo: {args.parallel} (max_workers={args.max_workers})")
    if args.group:
        logger.info(f"  Filtro por grupo: {args.group}")
    if args.scraper:
        logger.info(f"  Filtro por scraper: {args.scraper}")
    logger.info("=" * 70)

    # Carrega credenciais do Databricks Secret Scope
    loaded = load_secrets(scope=args.secret_scope)
    if loaded:
        logger.info(f"Credenciais configuradas ({len(loaded)}): {', '.join(loaded.keys())}")
    else:
        logger.info("Nenhum segredo específico carregado do Secret Scope ou variáveis.")

    if args.skip_db:
        os.environ["SKIP_ORACLE_DB"] = "1"
        logger.info("Persistência em banco Oracle desabilitada (--skip-db).")

    # Importa módulos do projeto agora que sys.path e variáveis estão estabelecidos
    from utils.paths import get_data_dir

    logger.info(f"Diretório de dados ativo: {get_data_dir()}")
    get_data_dir().mkdir(parents=True, exist_ok=True)

    if args.generate_catalog:
        from scripts.generate_catalog import generate

        logger.info("Gerando catálogo de datasets...")
        generate()
        logger.info("✔ Catálogo gerado com sucesso.")
        return

    # Importa orquestrador central sem duplicar código
    import run_all

    start_time = time.time()
    try:
        run_all.main(
            group=args.group,
            scraper=args.scraper,
            parallel=args.parallel,
            max_workers=args.max_workers,
        )
    except SystemExit as se:
        if se.code != 0:
            logger.error(f"O pipeline concluiu com código de erro {se.code}")
            sys.exit(se.code)
    except Exception as e:
        logger.error(f"Erro fatal durante a execução do pipeline: {e}", exc_info=True)
        sys.exit(1)

    # Em execuções completas (sem filtro), executa scripts complementares do ciclo
    if not args.group and not args.scraper:
        try:
            logger.info("Gerando JSON consolidado para tela de consulta...")
            from scripts.gerar_consulta_json import main as gerar_consulta

            gerar_consulta()
            logger.info("✔ JSON de consulta atualizado com sucesso.")
        except Exception as e:
            logger.warning(f"Falha ao gerar JSON de consulta: {e}")

    # Exportação opcional para Delta Lake
    if args.export_delta:
        logger.info("Exportando dados gerados para Delta Lake...")
        try:
            from databricks.delta_exporter import export_csv_to_delta

            summary = export_csv_to_delta(
                catalog_name=args.delta_catalog,
                schema_name=args.delta_schema,
                data_dir=get_data_dir(),
                write_mode="overwrite",
            )
            logger.info(f"✔ Exportação para Delta Lake concluída: {summary.get('total_files', 0)} arquivos.")
        except Exception as e:
            logger.error(f"Falha ao exportar para Delta Lake: {e}", exc_info=True)

    elapsed = time.time() - start_time
    logger.info("=" * 70)
    logger.info(f"✔ Job Databricks concluído com sucesso em {elapsed:.1f}s.")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
