window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-11-21T01:54:27.830005",
  "elapsed_seconds": 97.75144076347351,
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
      "elapsed_seconds": 11.912862300872803,
      "error": null,
      "timestamp": "2026-11-21T01:54:27.830143"
    },
    "standard_and_poors_emissores": {
      "status": "error",
      "elapsed_seconds": 30.93607449531555,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_emissores.\n",
      "timestamp": "2026-11-21T01:54:27.830145"
    },
    "moodys_emissores": {
      "status": "error",
      "elapsed_seconds": 7.503631353378296,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_emissores.\n",
      "timestamp": "2026-11-21T01:54:27.830135"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 41.52471137046814,
      "error": null,
      "timestamp": "2026-11-21T01:54:27.830156"
    },
    "moodys_ratings": {
      "status": "error",
      "elapsed_seconds": 6.8620007038116455,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper moodys_ratings.\n",
      "timestamp": "2026-11-21T01:54:27.830151"
    },
    "standard_and_poors_ratings": {
      "status": "error",
      "elapsed_seconds": 24.857733249664307,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/run_all.py\", line 87, in run_scraper\n    scraper.run()\n    ~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 118, in run\n    raise e\n  File \"/home/runner/work/PulseRatingsBrasil/PulseRatingsBrasil/scrapers/utils/base.py\", line 45, in run\n    raise RuntimeError(msg)\nRuntimeError: Nenhum dado retornado para salvar pelo scraper standard_and_poors_ratings.\n",
      "timestamp": "2026-11-21T01:54:27.830154"
    },
    "austin_emissores": {
      "status": "success",
      "elapsed_seconds": 1.353635549545288,
      "error": null,
      "timestamp": "2026-11-21T01:54:27.830141"
    },
    "austin_ratings": {
      "status": "success",
      "elapsed_seconds": 17.278944730758667,
      "error": null,
      "timestamp": "2026-11-21T01:54:27.830153"
    },
    "liberum_emissores": {
      "status": "success",
      "elapsed_seconds": 47.29912209510803,
      "error": null,
      "timestamp": "2026-11-21T01:54:27.830147"
    },
    "liberum_ratings": {
      "status": "success",
      "elapsed_seconds": 56.22435808181763,
      "error": null,
      "timestamp": "2026-11-21T01:54:27.830149"
    }
  },
  "drifts": {}
};
