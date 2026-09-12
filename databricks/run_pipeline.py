#!/usr/bin/env python3
"""
Pulse Ratings Brasil – Wrapper de compatibilidade para Databricks
Redireciona para databricks/run_pulse_ratings_brasil_job.py mantendo retrocompatibilidade.
"""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from run_pulse_ratings_brasil_job import main

if __name__ == "__main__":
    main()
