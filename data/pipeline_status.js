window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-19T15:33:34.954011",
  "elapsed_seconds": 1864.4766051769257,
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
      "elapsed_seconds": 11.233161687850952,
      "error": null,
      "timestamp": "2026-11-19T15:33:34.954201"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 31.964884042739868,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-19T15:33:34.954197"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 814.7763080596924,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-19T15:33:34.954209"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 39.58083963394165,
      "error": null,
      "timestamp": "2026-11-19T15:33:34.954216"
    },
    "moodys_ratings": {
      "status": "error",
      "elapsed_seconds": 1048.399401664734,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_ratings.\n",
      "timestamp": "2026-11-19T15:33:34.954218"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 18.811393976211548,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-19T15:33:34.954211"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.2973580360412598,
      "error": null,
      "timestamp": "2026-11-19T15:33:34.954190"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 19.088021755218506,
      "error": null,
      "timestamp": "2026-11-19T15:33:34.954214"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 61.804654359817505,
      "error": null,
      "timestamp": "2026-11-19T15:33:34.954203"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 61.85727787017822,
      "error": null,
      "timestamp": "2026-11-19T15:33:34.954206"
    }
  },
  "drifts": {}
};
