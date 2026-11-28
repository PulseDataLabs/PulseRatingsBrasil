window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-28T03:12:05.102236",
  "elapsed_seconds": 2138.5027375221252,
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
      "elapsed_seconds": 12.069183588027954,
      "error": null,
      "timestamp": "2026-11-28T03:12:05.102410"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.106242418289185,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-28T03:12:05.102420"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 1189.3892686367035,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-28T03:12:05.102429"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 37.77721667289734,
      "error": null,
      "timestamp": "2026-11-28T03:12:05.102436"
    },
    "moodys_ratings": {
      "status": "error",
      "elapsed_seconds": 949.1087665557861,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_ratings.\n",
      "timestamp": "2026-11-28T03:12:05.102438"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 21.926748514175415,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-28T03:12:05.102434"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.118572473526001,
      "error": null,
      "timestamp": "2026-11-28T03:12:05.102416"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 20.795574188232422,
      "error": null,
      "timestamp": "2026-11-28T03:12:05.102431"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 31.61055874824524,
      "error": null,
      "timestamp": "2026-11-28T03:12:05.102423"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 44.805641412734985,
      "error": null,
      "timestamp": "2026-11-28T03:12:05.102426"
    }
  },
  "drifts": {}
};
