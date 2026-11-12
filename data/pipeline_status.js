window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-12T18:54:50.873572",
  "elapsed_seconds": 835.8859553337097,
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
      "elapsed_seconds": 11.621966123580933,
      "error": null,
      "timestamp": "2026-11-12T18:54:50.873671"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.24121618270874,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-12T18:54:50.873669"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 784.3582935333252,
      "error": null,
      "timestamp": "2026-11-12T18:54:50.873676"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 41.2945442199707,
      "error": null,
      "timestamp": "2026-11-12T18:54:50.873680"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 50.15532922744751,
      "error": null,
      "timestamp": "2026-11-12T18:54:50.873682"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 29.05767560005188,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-12T18:54:50.873679"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.369476318359375,
      "error": null,
      "timestamp": "2026-11-12T18:54:50.873664"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 18.42590641975403,
      "error": null,
      "timestamp": "2026-11-12T18:54:50.873677"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 56.35973405838013,
      "error": null,
      "timestamp": "2026-11-12T18:54:50.873673"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 56.40899848937988,
      "error": null,
      "timestamp": "2026-11-12T18:54:50.873675"
    }
  },
  "drifts": {}
};
