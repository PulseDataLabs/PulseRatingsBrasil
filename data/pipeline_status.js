window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-16T16:41:34.026086",
  "elapsed_seconds": 1079.2588708400726,
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
      "elapsed_seconds": 12.03784465789795,
      "error": null,
      "timestamp": "2026-11-16T16:41:34.026185"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 33.28943347930908,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-16T16:41:34.026183"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 995.2023541927338,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-16T16:41:34.026190"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 41.46005153656006,
      "error": null,
      "timestamp": "2026-11-16T16:41:34.026192"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 65.33288621902466,
      "error": null,
      "timestamp": "2026-11-16T16:41:34.026193"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 25.58738350868225,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-16T16:41:34.026191"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 3.4334490299224854,
      "error": null,
      "timestamp": "2026-11-16T16:41:34.026179"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 80.61950254440308,
      "error": null,
      "timestamp": "2026-11-16T16:41:34.026194"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 57.209319829940796,
      "error": null,
      "timestamp": "2026-11-16T16:41:34.026187"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 57.26216411590576,
      "error": null,
      "timestamp": "2026-11-16T16:41:34.026188"
    }
  },
  "drifts": {}
};
