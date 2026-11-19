window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-19T02:10:09.376751",
  "elapsed_seconds": 93.1143651008606,
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
      "elapsed_seconds": 11.024362325668335,
      "error": null,
      "timestamp": "2026-11-19T02:10:09.376854"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 30.589998245239258,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-19T02:10:09.376851"
    },
    "moodys_emissores": {
      "status": "success",
      "elapsed_seconds": 35.169607639312744,
      "error": null,
      "timestamp": "2026-11-19T02:10:09.376852"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 39.94403791427612,
      "error": null,
      "timestamp": "2026-11-19T02:10:09.376860"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 45.48417782783508,
      "error": null,
      "timestamp": "2026-11-19T02:10:09.376861"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 21.82981300354004,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-19T02:10:09.376859"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.4233829975128174,
      "error": null,
      "timestamp": "2026-11-19T02:10:09.376847"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 17.454883337020874,
      "error": null,
      "timestamp": "2026-11-19T02:10:09.376858"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 47.4152774810791,
      "error": null,
      "timestamp": "2026-11-19T02:10:09.376855"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 47.62719440460205,
      "error": null,
      "timestamp": "2026-11-19T02:10:09.376857"
    }
  },
  "drifts": {}
};
