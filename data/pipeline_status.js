window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-20T02:03:30.531394",
  "elapsed_seconds": 363.8646903038025,
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
      "elapsed_seconds": 10.90328311920166,
      "error": null,
      "timestamp": "2026-11-20T02:03:30.531488"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 30.94068455696106,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-20T02:03:30.531489"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 321.5642206668854,
      "error": null,
      "timestamp": "2026-11-20T02:03:30.531493"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 40.80624985694885,
      "error": null,
      "timestamp": "2026-11-20T02:03:30.531496"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 42.298386096954346,
      "error": null,
      "timestamp": "2026-11-20T02:03:30.531497"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 25.817092180252075,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-20T02:03:30.531495"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.5126299858093262,
      "error": null,
      "timestamp": "2026-11-20T02:03:30.531485"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 15.701087474822998,
      "error": null,
      "timestamp": "2026-11-20T02:03:30.531494"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 56.09144949913025,
      "error": null,
      "timestamp": "2026-11-20T02:03:30.531491"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 57.716904163360596,
      "error": null,
      "timestamp": "2026-11-20T02:03:30.531492"
    }
  },
  "drifts": {}
};
