import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJECT = _HERE.parent


def test_run_pipeline_dry_run_fitch_emissores(tmp_path):
    """Executa o pipeline Databricks com --dry-run e --scraper fitch_emissores."""
    data_dir = tmp_path / "databricks_test"
    env = {
        **os.environ,
        "DATABRICKS_DATA_PATH": str(data_dir),
        "PYTHONPATH": str(_PROJECT),
    }
    result = subprocess.run(
        [
            sys.executable,
            str(_PROJECT / "databricks" / "run_pipeline.py"),
            "--dry-run",
            "--scraper",
            "fitch_emissores",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "fitch_emissores" in output
    assert "DRY-RUN" in output


def test_run_pipeline_dry_run_all(tmp_path):
    """Executa o pipeline Databricks completo com --dry-run."""
    data_dir = tmp_path / "databricks_all"
    env = {
        **os.environ,
        "DATABRICKS_DATA_PATH": str(data_dir),
        "PYTHONPATH": str(_PROJECT),
    }
    result = subprocess.run(
        [
            sys.executable,
            str(_PROJECT / "databricks" / "run_pipeline.py"),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "DRY-RUN" in output
