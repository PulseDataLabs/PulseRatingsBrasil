window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-27T03:20:59.027263",
  "elapsed_seconds": 1524.7066669464111,
  "status": "error",
  "summary": {
    "total": 10,
    "success": 7,
    "failed": 3,
    "drifts": 0
  },
  "scrapers": {
    "fitch_emissores": {
      "status": "success",
      "elapsed_seconds": 13.324519157409668,
      "error": null,
      "timestamp": "2026-11-27T03:20:59.027354"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.198685884475708,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-27T03:20:59.027360"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 1170.7965064048767,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-27T03:20:59.027365"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 41.09188222885132,
      "error": null,
      "timestamp": "2026-11-27T03:20:59.027369"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 353.9045081138611,
      "error": null,
      "timestamp": "2026-11-27T03:20:59.027370"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 18.36466884613037,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-27T03:20:59.027368"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.1497366428375244,
      "error": null,
      "timestamp": "2026-11-27T03:20:59.027358"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 14.080292463302612,
      "error": null,
      "timestamp": "2026-11-27T03:20:59.027366"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 41.05011320114136,
      "error": null,
      "timestamp": "2026-11-27T03:20:59.027362"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 55.5709342956543,
      "error": null,
      "timestamp": "2026-11-27T03:20:59.027364"
    }
  },
  "drifts": {}
};
