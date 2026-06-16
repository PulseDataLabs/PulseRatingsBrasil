import os
from pathlib import Path

from utils.paths import get_data_dir


def test_get_data_dir_default():
    """Sem DATABRICKS_DATA_PATH, deve retornar data/ relativo ao projeto."""
    if "DATABRICKS_DATA_PATH" in os.environ:
        del os.environ["DATABRICKS_DATA_PATH"]
    result = get_data_dir()
    assert result.name == "data"
    assert result.is_absolute()


def test_get_data_dir_custom():
    """Com DATABRICKS_DATA_PATH, deve retornar o path definido."""
    os.environ["DATABRICKS_DATA_PATH"] = "/tmp/teste_data_dir"
    try:
        result = get_data_dir()
        assert result == Path("/tmp/teste_data_dir")
    finally:
        del os.environ["DATABRICKS_DATA_PATH"]


def test_get_data_dir_via_data_dir():
    """DATA_DIR tem prioridade sobre DATABRICKS_DATA_PATH."""
    os.environ["DATA_DIR"] = "/opt/dados"
    os.environ["DATABRICKS_DATA_PATH"] = "/tmp/ignorado"
    try:
        result = get_data_dir()
        assert result == Path("/opt/dados")
    finally:
        del os.environ["DATA_DIR"]
        del os.environ["DATABRICKS_DATA_PATH"]


def test_get_data_dir_custom_relative(tmp_path):
    """Com DATABRICKS_DATA_PATH relativo, deve retornar como Path."""
    target = tmp_path / "dbfs" / "data"
    os.environ["DATABRICKS_DATA_PATH"] = str(target)
    try:
        result = get_data_dir()
        assert result == target
    finally:
        del os.environ["DATABRICKS_DATA_PATH"]
