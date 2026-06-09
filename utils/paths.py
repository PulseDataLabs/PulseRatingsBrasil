import os
from pathlib import Path


def get_data_dir() -> Path:
    raw = os.environ.get("DATABRICKS_DATA_PATH")
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[1] / "data"
