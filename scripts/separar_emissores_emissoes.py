#!/usr/bin/env python
"""
Separa ratings consolidados de todas as agências em duas tabelas:
1. data/ratings_emissores.csv (Ratings de nível de entidade/emissor)
2. data/ratings_emissoes.csv (Ratings de nível de emissão/instrumento)

Faz mapeamento de chaves (no_emissor_padronizado) e vinculação de devedores.
"""

import csv
import logging
import re
import sys
from pathlib import Path

# Configura caminhos para permitir importações
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from scripts.consolidar_emissores import normalizar
from utils.base import salvar_csv
from utils.paths import get_data_dir

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("separar_emissores_emissoes")

DEBTOR_ALIASES = {
    "DASA": "DIAGNOSTICOS AMERICA",
    "LOCALIZA": "LOCALIZA RENT CAR",
    "COGNA": "COGNA EDUCACAO",
    "MULTIPLAN": "MULTIPLAN EMPREENDIMENTOS IMOBILIARIOS",
    "ARMAC": "ARMAC LOCACAO",
    "CSN": "COMPANHIA SIDERURGICA NACIONAL",
    "TAESA": "TRANSMISSORA ALIANCA DE ENERGIA ELETRICA",
    "PETROBRAS": "PETROLEO BRASILEIRO",
    "VIVEO": "CM HOSPITALAR",
    "JBS": "JBS",
    "BRF": "BRF",
}


def find_matching_issuer(
    raw_name: str, consolidated_names: set, consolidated_list: list, return_fallback: bool = True
) -> str:
    """Normaliza o nome do emissor e tenta encontrar o correspondente padronizado."""
    if not raw_name:
        return ""
    norm = normalizar(raw_name)
    if not norm:
        return ""

    # 1. Match exato
    if norm in consolidated_names:
        return norm

    # 2. Check se o nome normalizado é prefixo de algum nome consolidado
    matches = [name for name in consolidated_list if name.startswith(norm)]
    if matches:
        return min(matches, key=len)

    # 3. Check se algum nome consolidado é prefixo do normalizado
    matches = [name for name in consolidated_list if norm.startswith(name)]
    if matches:
        return max(matches, key=len)

    # 4. Match de substring
    matches = [name for name in consolidated_list if norm in name or name in norm]
    if matches:
        return min(matches, key=len)

    return norm if return_fallback else ""


def extract_linked_debtor(raw_name: str, consolidated_names: set, consolidated_list: list) -> str:
    """Extrai texto entre parênteses do nome da emissão para tentar achar o devedor corporativo."""
    if not raw_name:
        return ""

    # Procura texto dentro de parênteses (ex: "Eco Securitizadora ... (JBS)")
    matches_paren = re.findall(r"\(([^)]+)\)", raw_name)
    if not matches_paren:
        return ""

    # Pega o último texto em parênteses
    candidate = matches_paren[-1].strip()

    # 1. Ignorar se contiver termos de série, classe, emissão, etc. (case-insensitive)
    ignore_terms = [
        "serie",
        "emissao",
        "classe",
        "sf",
        "f1",
        "f2",
        "f3",
        "lote",
        "tranche",
        "subordinada",
        "senior",
        "meza",
    ]
    candidate_lower = candidate.lower()
    if any(term in candidate_lower for term in ignore_terms):
        return ""

    # 2. Ignorar se for apenas números ou caracteres especiais
    if re.match(r"^[\d\s\.,ª°\-\/]+$", candidate):
        return ""

    norm_candidate = normalizar(candidate)
    if not norm_candidate or len(norm_candidate) < 3:
        return ""

    # Ignora parênteses que são claramente séries, tranches, datas ou classes ou palavras genéricas
    generic_terms = {
        "SERIE",
        "EMISSAO",
        "CLASSE",
        "LOCAL",
        "SF",
        "F1",
        "F2",
        "F3",
        "AAA",
        "AA",
        "BBB",
        "FIDC",
        "FIDCS",
        "CRI",
        "CRIS",
        "CRA",
        "CRAS",
        "BANCO",
        "BANCOS",
        "COOPERATIVA",
        "SECURITIZADORA",
        "CIA",
        "COMPANHIA",
        "FUNDO",
        "FUNDOS",
        "INVESTIMENTO",
        "CREDITO",
        "SECURITIZACAO",
        "S/A",
        "SA",
        "LTDA",
    }
    if norm_candidate in generic_terms or any(
        term in norm_candidate for term in ["SERIE", "EMISSAO", "CLASSE"]
    ):
        return ""

    # Se estiver nos aliases mapeados
    if norm_candidate in DEBTOR_ALIASES:
        return DEBTOR_ALIASES[norm_candidate]

    # Busca no catálogo, sem usar o fallback bruto
    matched = find_matching_issuer(candidate, consolidated_names, consolidated_list, return_fallback=False)

    # Se o nome retornado for uma palavra genérica ou muito curta, descarta
    if matched in generic_terms or len(matched) < 3:
        return ""

    return matched


def main():
    data_dir = get_data_dir()
    emissores_consolidado_path = data_dir / "emissores_consolidado.csv"

    if not emissores_consolidado_path.exists():
        logger.error(f"Arquivo {emissores_consolidado_path} não encontrado. Abortando.")
        sys.exit(1)

    # 1. Carrega os emissores consolidados
    consolidated_list = []
    with open(emissores_consolidado_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            p = row.get("no_emissor_padronizado")
            if p:
                consolidated_list.append(p.strip())
    consolidated_names = set(consolidated_list)
    logger.info(f"Carregados {len(consolidated_names)} emissores consolidados de referência.")

    # 2. Configurações dos caminhos das fontes
    fontes = {
        "Austin": {
            "path": data_dir / "austin_ratings.csv",
            "type_col": "no_tipo_rating",
            "val_col": "de_rating_br",
            "outlook_col": "de_outlook",
            "date_col": "dt_acao_rating",
            "link_col": "link",
            "instr_col": None,
        },
        "Fitch": {
            "path": data_dir / "fitch_ratings.csv",
            "type_col": "no_tipo_rating",
            "val_col": "de_rating_br",
            "outlook_col": "de_outlook",
            "date_col": "dt_acao_rating",
            "link_col": "link",
            "instr_col": "de_instrumento",
        },
        "Liberum": {
            "path": data_dir / "liberum_ratings.csv",
            "type_col": "no_tipo_rating",
            "val_col": "de_rating_br",
            "outlook_col": "de_outlook",
            "date_col": "dt_acao_rating",
            "link_col": "link",
            "instr_col": "de_classe",  # de_classe + de_escala será usado
        },
        "Moody's": {
            "path": data_dir / "moodys_ratings.csv",
            "type_col": "no_tipo_rating",
            "val_col": "de_rating_br",
            "outlook_col": "de_outlook",
            "date_col": "dt_rating",
            "link_col": None,
            "instr_col": "de_instrumento",
        },
        "S&P": {
            "path": data_dir / "standard_and_poors_ratings.csv",
            "type_col": "no_tipo_rating",
            "val_col": "de_rating_br",
            "outlook_col": "de_outlook",
            "date_col": "dt_acao_rating",
            "link_col": "link",
            "instr_col": None,
        },
    }

    rows_emissores = []
    rows_emissoes = []

    # 3. Processamento das agências
    for agencia, config in fontes.items():
        csv_path = config["path"]
        if not csv_path.exists():
            logger.warning(f"Arquivo da agência {agencia} não encontrado: {csv_path}")
            continue

        logger.info(f"Processando ratings da agência {agencia}...")

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                dt_captura = row.get("dt_captura") or ""
                no_emissor_original = row.get("no_emissor") or ""
                no_tipo_rating = row.get(config["type_col"]) or ""
                de_rating_br = row.get(config["val_col"]) or ""
                de_outlook = row.get(config["outlook_col"]) or ""
                dt_acao_rating = row.get(config["date_col"]) or ""
                link = row.get(config["link_col"]) if config["link_col"] else ""

                # Identifica se é emissão ou emissor
                is_emissao = False
                de_instrumento = ""

                if agencia == "Austin":
                    if no_tipo_rating in ["FIDCs", "CRIs", "Debêntures"]:
                        is_emissao = True
                        if " - " in no_emissor_original:
                            base_emissor, de_instrumento = no_emissor_original.split(" - ", 1)
                            de_instrumento = de_instrumento.strip()
                        elif " – " in no_emissor_original:
                            base_emissor, de_instrumento = no_emissor_original.split(" – ", 1)
                            de_instrumento = de_instrumento.strip()
                        else:
                            base_emissor = no_emissor_original
                            de_instrumento = no_tipo_rating
                elif agencia == "Fitch":
                    de_instrumento_val = row.get("de_instrumento") or ""
                    if de_instrumento_val:
                        is_emissao = True
                        de_instrumento = de_instrumento_val
                elif agencia == "Liberum":
                    if no_tipo_rating in ["FIDC", "CRI", "CRA", "Debenture Colateralizada"]:
                        is_emissao = True
                        de_classe = row.get("de_classe") or ""
                        de_escala = row.get("de_escala") or ""
                        de_instrumento = f"{de_classe} - {de_escala}".strip(" -")
                elif agencia == "Moody's" and no_tipo_rating in [
                    "Rating de Dívida",
                    "Rating de Operação Estruturada",
                ]:
                    is_emissao = True
                    de_instrumento = row.get("de_instrumento") or ""

                # Mapeia emissor padronizado
                lookup_nome = base_emissor if (agencia == "Austin" and is_emissao) else no_emissor_original
                no_emissor_padronizado = find_matching_issuer(
                    lookup_nome, consolidated_names, consolidated_list
                )

                if is_emissao:
                    # Tenta extrair o devedor corporativo final se for um CRI/CRA ou FIDC securitizado
                    no_devedor_vinculado = extract_linked_debtor(
                        no_emissor_original, consolidated_names, consolidated_list
                    )

                    rows_emissoes.append(
                        {
                            "dt_captura": dt_captura,
                            "agencia": agencia,
                            "no_emissor_padronizado": no_emissor_padronizado,
                            "no_emissor_original": no_emissor_original,
                            "no_tipo_rating": no_tipo_rating,
                            "de_instrumento": de_instrumento,
                            "de_rating_br": de_rating_br,
                            "de_outlook": de_outlook,
                            "dt_acao_rating": dt_acao_rating,
                            "link": link,
                            "no_devedor_vinculado": no_devedor_vinculado,
                        }
                    )
                else:
                    rows_emissores.append(
                        {
                            "dt_captura": dt_captura,
                            "agencia": agencia,
                            "no_emissor_padronizado": no_emissor_padronizado,
                            "no_emissor_original": no_emissor_original,
                            "no_tipo_rating": no_tipo_rating,
                            "de_rating_br": de_rating_br,
                            "de_outlook": de_outlook,
                            "dt_acao_rating": dt_acao_rating,
                            "link": link,
                        }
                    )

    # 4. Grava os novos arquivos CSV
    colunas_emissores = [
        "dt_captura",
        "agencia",
        "no_emissor_padronizado",
        "no_emissor_original",
        "no_tipo_rating",
        "de_rating_br",
        "de_outlook",
        "dt_acao_rating",
        "link",
    ]
    colunas_emissoes = [
        "dt_captura",
        "agencia",
        "no_emissor_padronizado",
        "no_emissor_original",
        "no_tipo_rating",
        "de_instrumento",
        "de_rating_br",
        "de_outlook",
        "dt_acao_rating",
        "link",
        "no_devedor_vinculado",
    ]

    out_emissores = data_dir / "ratings_emissores.csv"
    out_emissoes = data_dir / "ratings_emissoes.csv"

    logger.info(f"Salvando {len(rows_emissores)} ratings de emissores...")
    salvar_csv(
        arquivo=out_emissores,
        registros=rows_emissores,
        cabecalho=colunas_emissores,
        acumular=False,
    )

    logger.info(f"Salvando {len(rows_emissoes)} ratings de emissões...")
    salvar_csv(
        arquivo=out_emissoes,
        registros=rows_emissoes,
        cabecalho=colunas_emissoes,
        acumular=False,
    )


if __name__ == "__main__":
    main()
