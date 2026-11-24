window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-24T05:14:27.494244",
  "elapsed_seconds": 1999.3708658218384,
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
      "elapsed_seconds": 12.113456726074219,
      "error": null,
      "timestamp": "2026-11-24T05:14:27.494398"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 30.9350643157959,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-24T05:14:27.494406"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 986.6093561649323,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-24T05:14:27.494411"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 42.37417411804199,
      "error": null,
      "timestamp": "2026-11-24T05:14:27.494416"
    },
    "moodys_ratings": {
      "status": "error",
      "elapsed_seconds": 1012.7562770843506,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_ratings.\n",
      "timestamp": "2026-11-24T05:14:27.494417"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 17.54318857192993,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-24T05:14:27.494414"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.140470027923584,
      "error": null,
      "timestamp": "2026-11-24T05:14:27.494403"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 14.555254697799683,
      "error": null,
      "timestamp": "2026-11-24T05:14:27.494413"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 43.70022988319397,
      "error": null,
      "timestamp": "2026-11-24T05:14:27.494408"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 57.00252413749695,
      "error": null,
      "timestamp": "2026-11-24T05:14:27.494410"
    }
  },
  "drifts": {}
};
