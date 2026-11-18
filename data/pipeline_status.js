window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-18T15:27:05.922901",
  "elapsed_seconds": 2063.3540663719177,
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
      "elapsed_seconds": 9.998442649841309,
      "error": null,
      "timestamp": "2026-11-18T15:27:05.923092"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 30.80674934387207,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-18T15:27:05.923083"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 1030.8693795204163,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-18T15:27:05.923095"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 35.88520407676697,
      "error": null,
      "timestamp": "2026-11-18T15:27:05.923099"
    },
    "moodys_ratings": {
      "status": "error",
      "elapsed_seconds": 1031.1756880283356,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_ratings.\n",
      "timestamp": "2026-11-18T15:27:05.923104"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 16.9382266998291,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-18T15:27:05.923097"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.305298089981079,
      "error": null,
      "timestamp": "2026-11-18T15:27:05.923077"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 191.2555124759674,
      "error": null,
      "timestamp": "2026-11-18T15:27:05.923102"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 32.084086179733276,
      "error": null,
      "timestamp": "2026-11-18T15:27:05.923086"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 32.204898834228516,
      "error": null,
      "timestamp": "2026-11-18T15:27:05.923089"
    }
  },
  "drifts": {}
};
