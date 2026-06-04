window.PULSERATINGS_PIPELINE_STATUS = {
  "timestamp": "2026-06-04T18:03:46.153639",
  "elapsed_seconds": 500.1984100341797,
  "status": "warning",
  "summary": {
    "total": 6,
    "success": 6,
    "failed": 0,
    "drifts": 5
  },
  "scrapers": {
    "moodys_local_ratings": {
      "status": "success",
      "elapsed_seconds": 42.10388803482056,
      "error": null,
      "timestamp": "2026-06-04T17:35:16.936755"
    },
    "s_p_ratings_brasil": {
      "status": "success",
      "elapsed_seconds": 393.6080310344696,
      "error": null,
      "timestamp": "2026-06-04T17:35:16.936756"
    },
    "s_p_entidades_brasil": {
      "status": "success",
      "elapsed_seconds": 29.869667053222656,
      "error": null,
      "timestamp": "2026-06-04T17:35:16.936752"
    },
    "fitch_ratings_brasil": {
      "status": "success",
      "elapsed_seconds": 1.1629440784454346,
      "error": null,
      "timestamp": "2026-06-04T17:35:16.936746"
    },
    "fitch_entidades": {
      "status": "success",
      "elapsed_seconds": 1.117807149887085,
      "error": null,
      "timestamp": "2026-06-04T18:03:46.153729"
    },
    "standard_and_poors_entidades": {
      "status": "success",
      "elapsed_seconds": 28.68364381790161,
      "error": null,
      "timestamp": "2026-06-04T18:03:46.153732"
    },
    "moodys_entidades": {
      "status": "success",
      "elapsed_seconds": 41.72172713279724,
      "error": null,
      "timestamp": "2026-06-04T18:03:46.153734"
    },
    "fitch_ratings": {
      "status": "success",
      "elapsed_seconds": 1.5129508972167969,
      "error": null,
      "timestamp": "2026-06-04T18:03:46.153735"
    },
    "moodys_ratings": {
      "status": "success",
      "elapsed_seconds": 41.42584800720215,
      "error": null,
      "timestamp": "2026-06-04T18:03:46.153736"
    },
    "standard_and_poors_ratings": {
      "status": "success",
      "elapsed_seconds": 458.47558665275574,
      "error": null,
      "timestamp": "2026-06-04T18:03:46.153737"
    }
  },
  "drifts": {
    "fitch_entidades.csv": {
      "added": [],
      "removed": [
        "data_captura"
      ],
      "timestamp": "2026-06-04T17:55:27.071524"
    },
    "standard_and_poors_entidades.csv": {
      "added": [],
      "removed": [
        "data_captura"
      ],
      "timestamp": "2026-06-04T17:55:54.600220"
    },
    "moodys_entidades.csv": {
      "added": [],
      "removed": [
        "data_captura"
      ],
      "timestamp": "2026-06-04T17:56:07.675585"
    },
    "fitch_ratings.csv": {
      "added": [
        "no_entidade"
      ],
      "removed": [
        "nome"
      ],
      "timestamp": "2026-06-04T17:56:09.168159"
    },
    "standard_and_poors_ratings.csv": {
      "added": [
        "no_entidade"
      ],
      "removed": [
        "data_captura",
        "nome"
      ],
      "timestamp": "2026-06-04T18:03:46.150781"
    }
  }
};
