"""
Gera um JSON consolidado com todos os ratings por emissor para alimentar a tela de consulta.

Junta emissores_consolidado.csv com os ratings das 3 agências (Fitch, Moody's, S&P)
e produz um JSON flat pronto para consumo via DataTables.
"""

import csv
import json
import os
import re
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EMISSORES_PATH = os.path.join(DATA_DIR, "emissores_consolidado.csv")
FITCH_RATINGS_PATH = os.path.join(DATA_DIR, "fitch_ratings.csv")
MOODYS_RATINGS_PATH = os.path.join(DATA_DIR, "moodys_ratings.csv")
SP_RATINGS_PATH = os.path.join(DATA_DIR, "standard_and_poors_ratings.csv")
OUTPUT_PATH = os.path.join(DATA_DIR, "emissores_rating.json")


def _cnpj_fmt(cnpj: str) -> str:
    if not cnpj:
        return ""
    limpo = re.sub(r"\D", "", cnpj)
    if len(limpo) != 14:
        return limpo
    return f"{limpo[:2]}.{limpo[2:5]}.{limpo[5:8]}/{limpo[8:12]}-{limpo[12:]}"


def _trim(s: str) -> str:
    return s.strip() if s else ""


def carregar_emissores() -> list[dict]:
    emissores = []
    with open(EMISSORES_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nome_padrao = _trim(row.get("no_emissor_padronizado", ""))
            if not nome_padrao:
                continue
            emissores.append({
                "no_emissor_padronizado": nome_padrao,
                "no_emissor_fitch": _trim(row.get("no_emissor_fitch", "")),
                "no_emissor_moodys": _trim(row.get("no_emissor_moodys", "")),
                "no_emissor_standard_and_poors": _trim(row.get("no_emissor_standard_and_poors", "")),
                "cnpj": _cnpj_fmt(row.get("cnpj_emissor", "")),
            })
    return emissores


def carregar_ratings(path: str) -> list[dict]:
    ratings = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ratings.append({k: _trim(v) for k, v in row.items()})
    return ratings


def build_index(ratings: list[dict], key: str) -> dict[str, list[dict]]:
    idx = defaultdict(list)
    for r in ratings:
        nome = r.get(key, "")
        if nome:
            idx[nome.upper()].append(r)
    return dict(idx)


def main() -> None:
    emissores = carregar_emissores()
    print(f"Emissores carregados: {len(emissores)}")

    fitch_ratings = carregar_ratings(FITCH_RATINGS_PATH)
    moodys_ratings = carregar_ratings(MOODYS_RATINGS_PATH)
    sp_ratings = carregar_ratings(SP_RATINGS_PATH)
    print(f"Ratings carregados: Fitch={len(fitch_ratings)}, Moody's={len(moodys_ratings)}, S&P={len(sp_ratings)}")

    fitch_idx = build_index(fitch_ratings, "no_emissor")
    moodys_idx = build_index(moodys_ratings, "no_emissor")
    sp_idx = build_index(sp_ratings, "no_emissor")

    resultados = []
    sem_match_fitch = 0
    sem_match_moodys = 0
    sem_match_sp = 0
    com_rating = 0

    for em in emissores:
        nome_padrao = em["no_emissor_padronizado"]
        cnpj = em["cnpj"]

        agencias = [
            ("Fitch", em["no_emissor_fitch"], fitch_idx),
            ("Moody's", em["no_emissor_moodys"], moodys_idx),
            ("S&P", em["no_emissor_standard_and_poors"], sp_idx),
        ]

        tem_rating = False

        for nome_agencia, nome_emissor, idx in agencias:
            if not nome_emissor:
                continue
            ratings = idx.get(nome_emissor.upper(), [])
            if not ratings:
                if nome_agencia == "Fitch":
                    sem_match_fitch += 1
                elif nome_agencia == "Moody's":
                    sem_match_moodys += 1
                else:
                    sem_match_sp += 1
                continue

            tem_rating = True
            for r in ratings:
                if nome_agencia == "Moody's":
                    row = {
                        "emissor": nome_padrao,
                        "cnpj": cnpj,
                        "agencia": "Moody's",
                        "tipo_rating": r.get("no_tipo_rating", ""),
                        "rating": r.get("de_rating_br", ""),
                        "outlook": r.get("de_outlook", ""),
                        "dt_acao": r.get("dt_rating", ""),
                        "setor": r.get("no_setor", ""),
                        "instrumento": r.get("de_instrumento", ""),
                        "link": "",
                    }
                elif nome_agencia == "S&P":
                    row = {
                        "emissor": nome_padrao,
                        "cnpj": cnpj,
                        "agencia": "S&P",
                        "tipo_rating": r.get("no_tipo_rating", ""),
                        "rating": r.get("de_rating_br", ""),
                        "outlook": r.get("de_outlook", ""),
                        "dt_acao": r.get("dt_acao_rating", ""),
                        "setor": "",
                        "instrumento": "",
                        "link": r.get("link", ""),
                    }
                else:
                    row = {
                        "emissor": nome_padrao,
                        "cnpj": cnpj,
                        "agencia": "Fitch",
                        "tipo_rating": r.get("no_tipo_rating", ""),
                        "rating": r.get("de_rating_br", ""),
                        "outlook": r.get("de_outlook", ""),
                        "dt_acao": r.get("dt_acao_rating", ""),
                        "setor": "",
                        "instrumento": "",
                        "link": r.get("link", ""),
                    }
                resultados.append(row)

        if tem_rating:
            com_rating += 1

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    total_emissores = len(emissores)
    print(f"\nJSON salvo: {OUTPUT_PATH}")
    print(f"Total de linhas (ratings): {len(resultados)}")
    print(f"Emissores com ao menos 1 rating: {com_rating} de {total_emissores}")
    print(f"Sem match Fitch: {sem_match_fitch}")
    print(f"Sem match Moody's: {sem_match_moodys}")
    print(f"Sem match S&P: {sem_match_sp}")


if __name__ == "__main__":
    main()
