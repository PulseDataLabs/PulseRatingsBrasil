window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-18T19:36:27.679892",
  "elapsed_seconds": 546.8862934112549,
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
      "elapsed_seconds": 11.187991619110107,
      "error": null,
      "timestamp": "2026-11-18T19:36:27.679989"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.088624238967896,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-18T19:36:27.679991"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 502.765252828598,
      "error": null,
      "timestamp": "2026-11-18T19:36:27.679995"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 39.19626045227051,
      "error": null,
      "timestamp": "2026-11-18T19:36:27.679998"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 44.11873507499695,
      "error": null,
      "timestamp": "2026-11-18T19:36:27.679999"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 23.388282537460327,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-18T19:36:27.679997"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.6620502471923828,
      "error": null,
      "timestamp": "2026-11-18T19:36:27.679986"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 16.13645839691162,
      "error": null,
      "timestamp": "2026-11-18T19:36:27.679996"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 58.281821966171265,
      "error": null,
      "timestamp": "2026-11-18T19:36:27.679993"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 59.9900438785553,
      "error": null,
      "timestamp": "2026-11-18T19:36:27.679994"
    }
  },
  "drifts": {}
};
