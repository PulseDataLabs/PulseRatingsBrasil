window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-10T14:04:15.875870",
  "elapsed_seconds": 731.4538841247559,
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
      "elapsed_seconds": 13.084887266159058,
      "error": null,
      "timestamp": "2026-11-10T14:04:15.876014"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 30.829123735427856,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-10T14:04:15.876011"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 643.6179487705231,
      "error": null,
      "timestamp": "2026-11-10T14:04:15.876021"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 42.22810411453247,
      "error": null,
      "timestamp": "2026-11-10T14:04:15.876031"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 67.39110946655273,
      "error": null,
      "timestamp": "2026-11-10T14:04:15.876036"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 35.43229150772095,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-10T14:04:15.876023"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 2.456451654434204,
      "error": null,
      "timestamp": "2026-11-10T14:04:15.876004"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 85.37553572654724,
      "error": null,
      "timestamp": "2026-11-10T14:04:15.876040"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 62.2110812664032,
      "error": null,
      "timestamp": "2026-11-10T14:04:15.876017"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 62.27356696128845,
      "error": null,
      "timestamp": "2026-11-10T14:04:15.876019"
    }
  },
  "drifts": {}
};
