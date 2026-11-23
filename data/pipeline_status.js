window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-23T18:00:24.669059",
  "elapsed_seconds": 136.7704999446869,
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
      "elapsed_seconds": 13.42843246459961,
      "error": null,
      "timestamp": "2026-11-23T18:00:24.669169"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.167721271514893,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-23T18:00:24.669177"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 53.248549699783325,
      "error": null,
      "timestamp": "2026-11-23T18:00:24.669179"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 42.979939222335815,
      "error": null,
      "timestamp": "2026-11-23T18:00:24.669188"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 72.55984234809875,
      "error": null,
      "timestamp": "2026-11-23T18:00:24.669190"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 34.247079372406006,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-23T18:00:24.669187"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.6342830657958984,
      "error": null,
      "timestamp": "2026-11-23T18:00:24.669175"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 23.89875626564026,
      "error": null,
      "timestamp": "2026-11-23T18:00:24.669185"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 49.074973344802856,
      "error": null,
      "timestamp": "2026-11-23T18:00:24.669182"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 64.20761799812317,
      "error": null,
      "timestamp": "2026-11-23T18:00:24.669183"
    }
  },
  "drifts": {}
};
