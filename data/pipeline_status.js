window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-24T17:36:59.327705",
  "elapsed_seconds": 2160.791988134384,
  "status": "error",
  "summary": {
    "total": 10,
    "success": 6,
    "failed": 4,
    "drifts": 0
  },
  "scrapers": {
    "fitch_emissores": {
      "status": "success",
      "elapsed_seconds": 11.968233823776245,
      "error": null,
      "timestamp": "2026-11-24T17:36:59.327848"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.21378183364868,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-24T17:36:59.327856"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 1047.649031162262,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-24T17:36:59.327863"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 39.29069948196411,
      "error": null,
      "timestamp": "2026-11-24T17:36:59.327868"
    },
    "moodys_ratings": {
      "status": "error",
      "elapsed_seconds": 1113.1357822418213,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_ratings.\n",
      "timestamp": "2026-11-24T17:36:59.327870"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 24.370375633239746,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-24T17:36:59.327866"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.4056663513183594,
      "error": null,
      "timestamp": "2026-11-24T17:36:59.327853"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 19.733416080474854,
      "error": null,
      "timestamp": "2026-11-24T17:36:59.327865"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 50.13858413696289,
      "error": null,
      "timestamp": "2026-11-24T17:36:59.327859"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 63.57890200614929,
      "error": null,
      "timestamp": "2026-11-24T17:36:59.327861"
    }
  },
  "drifts": {}
};
