window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-27T15:46:38.483143",
  "elapsed_seconds": 120.19882273674011,
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
      "elapsed_seconds": 11.98041558265686,
      "error": null,
      "timestamp": "2026-11-27T15:46:38.483236"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.5696542263031,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-27T15:46:38.483242"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 43.058730125427246,
      "error": null,
      "timestamp": "2026-11-27T15:46:38.483244"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 40.98486614227295,
      "error": null,
      "timestamp": "2026-11-27T15:46:38.483250"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 56.253291845321655,
      "error": null,
      "timestamp": "2026-11-27T15:46:38.483252"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 33.611682415008545,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-27T15:46:38.483249"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.3125247955322266,
      "error": null,
      "timestamp": "2026-11-27T15:46:38.483240"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 17.070331811904907,
      "error": null,
      "timestamp": "2026-11-27T15:46:38.483248"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 50.5969820022583,
      "error": null,
      "timestamp": "2026-11-27T15:46:38.483245"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 63.942891359329224,
      "error": null,
      "timestamp": "2026-11-27T15:46:38.483247"
    }
  },
  "drifts": {}
};
