window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-26T03:20:12.077420",
  "elapsed_seconds": 1064.8543765544891,
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
      "elapsed_seconds": 11.832061290740967,
      "error": null,
      "timestamp": "2026-11-26T03:20:12.077515"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.55688190460205,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-26T03:20:12.077519"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 1020.7057781219482,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-26T03:20:12.077526"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 40.009734869003296,
      "error": null,
      "timestamp": "2026-11-26T03:20:12.077529"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 44.14513635635376,
      "error": null,
      "timestamp": "2026-11-26T03:20:12.077531"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 24.113686561584473,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-26T03:20:12.077528"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.1640353202819824,
      "error": null,
      "timestamp": "2026-11-26T03:20:12.077521"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 15.745306730270386,
      "error": null,
      "timestamp": "2026-11-26T03:20:12.077527"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 46.38336682319641,
      "error": null,
      "timestamp": "2026-11-26T03:20:12.077523"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 58.38575196266174,
      "error": null,
      "timestamp": "2026-11-26T03:20:12.077524"
    }
  },
  "drifts": {}
};
