#!/usr/bin/env python
"""
Pulse Ratings Brasil – Pipeline para execução em Databricks

Uso:
    python databricks/run_pipeline.py                         # executa full pipeline
    python databricks/run_pipeline.py --dry-run               # apenas descobre + log, sem salvar
    python databricks/run_pipeline.py --scraper fitch_ratings # scraper específico
    python databricks/run_pipeline.py --group ratings         # grupo específico

Comportamento:
    - Lê DATABRICKS_DATA_PATH do .env (ou variável de ambiente)
    - Fallback para data/ se a variável não estiver definida
    - Usa o mesmo motor de descoberta de scrapers do run_all.py
"""

import argparse
import importlib
import logging
import sys
import time
from pathlib import Path

# Garante que o projeto está no sys.path para importação relativa
_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from dotenv import load_dotenv

load_dotenv()

from utils.paths import get_data_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("databricks_pipeline")


def discover_scrapers() -> dict[str, dict]:
    scrapers = {}
    scrapers_dir = _HERE / "scrapers"

    for file_path in scrapers_dir.glob("*.py"):
        module_name = file_path.stem
        if module_name in ("__init__", "generic_scraper"):
            continue

        try:
            mod = importlib.import_module(f"scrapers.{module_name}")
            class_name = "".join(word.capitalize() for word in module_name.split("_")) + "Scraper"

            if hasattr(mod, class_name):
                cls = getattr(mod, class_name)
                scrapers[module_name] = {
                    "group": getattr(cls, "group", "misc"),
                    "enabled": getattr(cls, "enabled", True),
                    "phase": getattr(cls, "phase", 1),
                    "class_name": class_name,
                    "title": getattr(cls, "title", module_name.replace("_", " ").title()),
                }
        except Exception as e:
            logger.warning(f"Erro ao carregar metadados do scraper {module_name}: {e}")

    return scrapers


def run_scraper(module_name: str, dry_run: bool = False) -> tuple[bool, float, str | None]:
    start = time.time()
    try:
        logger.info(f"▶  Executando: {module_name} (dry_run={dry_run})")
        mod = importlib.import_module(f"scrapers.{module_name}")
        class_name = "".join(word.capitalize() for word in module_name.split("_")) + "Scraper"

        if hasattr(mod, class_name):
            scraper = getattr(mod, class_name)()
            if dry_run:
                logger.info(f"[DRY-RUN] Scraper {module_name} seria executado, output em {get_data_dir()}")
            else:
                scraper.run()
        elif hasattr(mod, "main"):
            if dry_run:
                logger.info(f"[DRY-RUN] main() de {module_name} seria chamada")
            else:
                mod.main()
        else:
            msg = f"Módulo {module_name} não tem classe {class_name} nem main()"
            logger.error(msg)
            return False, time.time() - start, msg

        elapsed = time.time() - start
        logger.info(f"✔  {module_name} ({elapsed:.2f}s)")
        return True, elapsed, None
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"✖  Erro em {module_name}: {e}", exc_info=True)
        return False, elapsed, str(e)


def main(group: str | None = None, scraper: str | None = None, dry_run: bool = False):
    logger.info(f"Data directory: {get_data_dir()}")
    get_data_dir().mkdir(parents=True, exist_ok=True)

    registry = discover_scrapers()

    if scraper:
        targets = {scraper: registry[scraper]} if scraper in registry else {}
    else:
        targets = {
            n: i for n, i in registry.items() if i["enabled"] and (group is None or i["group"] == group)
        }

    if not targets:
        logger.error("Nenhum scraper encontrado para execução.")
        sys.exit(1)

    logger.info(f"{len(targets)} scraper(s) selecionado(s): {', '.join(targets)}")

    phase1 = [n for n, i in targets.items() if i["phase"] == 1]
    phase2 = [n for n, i in targets.items() if i["phase"] == 2]

    results: dict[str, tuple[bool, float, str | None]] = {}

    for name in phase1 + phase2:
        ok, elapsed, err = run_scraper(name, dry_run=dry_run)
        results[name] = (ok, elapsed, err)

    ok_count = sum(1 for r in results.values() if r[0])
    fail_count = sum(1 for r in results.values() if not r[0])

    logger.info(f"Pipeline concluído: {ok_count} ok, {fail_count} erro(s) em {len(results)} scraper(s)")

    if fail_count:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Ratings – Pipeline Databricks")
    parser.add_argument("--dry-run", action="store_true", help="Apenas log do que seria executado")
    parser.add_argument("--scraper", type=str, help="Executar apenas um scraper específico")
    parser.add_argument("--group", type=str, help="Executar apenas scrapers de um grupo")
    args = parser.parse_args()
    main(group=args.group, scraper=args.scraper, dry_run=args.dry_run)
