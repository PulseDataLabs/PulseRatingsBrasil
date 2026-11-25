window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-25T16:29:51.481512",
  "elapsed_seconds": 1739.7766811847687,
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
      "elapsed_seconds": 10.270417928695679,
      "error": null,
      "timestamp": "2026-11-25T16:29:51.481639"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.04888415336609,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-25T16:29:51.481654"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 1001.4438998699188,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-25T16:29:51.481656"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 35.68385291099548,
      "error": null,
      "timestamp": "2026-11-25T16:29:51.481661"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 738.3265657424927,
      "error": null,
      "timestamp": "2026-11-25T16:29:51.481663"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 18.752267360687256,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-25T16:29:51.481657"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.3016157150268555,
      "error": null,
      "timestamp": "2026-11-25T16:29:51.481646"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 35.68004894256592,
      "error": null,
      "timestamp": "2026-11-25T16:29:51.481659"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 19.31716823577881,
      "error": null,
      "timestamp": "2026-11-25T16:29:51.481649"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 30.959580898284912,
      "error": null,
      "timestamp": "2026-11-25T16:29:51.481651"
    }
  },
  "drifts": {}
};
