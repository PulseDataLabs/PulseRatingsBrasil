window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-19T19:45:00.943925",
  "elapsed_seconds": 768.8178384304047,
  "status": "error",
  "summary": {
    "total": 10,
    "success": 8,
    "failed": 2,
    "drifts": 0
  },
  "scrapers": {
    "fitch_emissores": {
      "status": "success",
      "elapsed_seconds": 10.500384092330933,
      "error": null,
      "timestamp": "2026-11-19T19:45:00.944053"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.09700608253479,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-19T19:45:00.944047"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 709.1963202953339,
      "error": null,
      "timestamp": "2026-11-19T19:45:00.944055"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 38.85490298271179,
      "error": null,
      "timestamp": "2026-11-19T19:45:00.944059"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 58.101219177246094,
      "error": null,
      "timestamp": "2026-11-19T19:45:00.944061"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 24.697351217269897,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-19T19:45:00.944058"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.5154609680175781,
      "error": null,
      "timestamp": "2026-11-19T19:45:00.944043"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 20.534862279891968,
      "error": null,
      "timestamp": "2026-11-19T19:45:00.944057"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 32.206395626068115,
      "error": null,
      "timestamp": "2026-11-19T19:45:00.944050"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 32.51485466957092,
      "error": null,
      "timestamp": "2026-11-19T19:45:00.944051"
    }
  },
  "drifts": {}
};
