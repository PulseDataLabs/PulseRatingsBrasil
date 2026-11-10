window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-10T02:21:46.879079",
  "elapsed_seconds": 92.92806577682495,
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
      "elapsed_seconds": 10.691097974777222,
      "error": null,
      "timestamp": "2026-11-10T02:21:46.879174"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 30.57317852973938,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-10T02:21:46.879171"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 31.46042561531067,
      "error": null,
      "timestamp": "2026-11-10T02:21:46.879173"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 39.45718216896057,
      "error": null,
      "timestamp": "2026-11-10T02:21:46.879180"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 45.861921548843384,
      "error": null,
      "timestamp": "2026-11-10T02:21:46.879181"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 25.05250334739685,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-10T02:21:46.879179"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.4874589443206787,
      "error": null,
      "timestamp": "2026-11-10T02:21:46.879168"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 16.307882070541382,
      "error": null,
      "timestamp": "2026-11-10T02:21:46.879178"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 47.02310609817505,
      "error": null,
      "timestamp": "2026-11-10T02:21:46.879176"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 47.063857316970825,
      "error": null,
      "timestamp": "2026-11-10T02:21:46.879177"
    }
  },
  "drifts": {}
};
