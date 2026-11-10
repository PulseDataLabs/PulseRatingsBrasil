window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-10T18:10:19.958091",
  "elapsed_seconds": 90.50767946243286,
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
      "elapsed_seconds": 11.171866655349731,
      "error": null,
      "timestamp": "2026-11-10T18:10:19.958186"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 30.688823699951172,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-10T18:10:19.958182"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 34.747194051742554,
      "error": null,
      "timestamp": "2026-11-10T18:10:19.958184"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 39.63592219352722,
      "error": null,
      "timestamp": "2026-11-10T18:10:19.958192"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 43.41481614112854,
      "error": null,
      "timestamp": "2026-11-10T18:10:19.958193"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 26.618601322174072,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-10T18:10:19.958191"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.5787906646728516,
      "error": null,
      "timestamp": "2026-11-10T18:10:19.958179"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 17.74115490913391,
      "error": null,
      "timestamp": "2026-11-10T18:10:19.958190"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 46.85821485519409,
      "error": null,
      "timestamp": "2026-11-10T18:10:19.958187"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 47.089346408843994,
      "error": null,
      "timestamp": "2026-11-10T18:10:19.958189"
    }
  },
  "drifts": {}
};
