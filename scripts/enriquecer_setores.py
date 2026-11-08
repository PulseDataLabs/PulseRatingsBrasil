"""
Enriquece os setores, subsetores e segmentos dos emissores em data/emissores_rating.json
e data/emissores_setores.json com base no mapeamento DE-PARA CVM/B3 e inferência por tipo de rating.
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from utils.paths import get_data_dir

logger = logging.getLogger("enriquecer_setores")

DE_PARA = {
    "Bancos": "Financeiro",
    "Emp. Adm. Part. - Bancos": "Financeiro",
    "Intermediação Financeira": "Financeiro",
    "Emp. Adm. Part. - Intermediação Financeira": "Financeiro",
    "Securitização de Recebíveis": "Financeiro",
    "Emp. Adm. Part. - Securitização de Recebíveis": "Financeiro",
    "Factoring": "Financeiro",
    "Crédito Imobiliário": "Financeiro",
    "Emp. Adm. Part. - Crédito Imobiliário": "Financeiro",
    "Arrendamento Mercantil": "Financeiro",
    "Emp. Adm. Part. - Arrendamento Mercantil": "Financeiro",
    "Bolsas de Valores/Mercadorias e Futuros": "Financeiro",
    "Emp. Adm. Part.-Bolsas de Valores/Mercadorias e Futuros": "Financeiro",
    "Seguradoras e Corretoras": "Financeiro",
    "Emp. Adm. Part. - Seguradoras e Corretoras": "Financeiro",
    "Energia Elétrica": "Utilidade Pública",
    "Emp. Adm. Part. - Energia Elétrica": "Utilidade Pública",
    "Saneamento, Serv. Água e Gás": "Utilidade Pública",
    "Emp. Adm. Part. - Saneamento, Serv. Água e Gás": "Utilidade Pública",
    "Alimentos": "Consumo não Cíclico",
    "Emp. Adm. Part. - Alimentos": "Consumo não Cíclico",
    "Bebidas e Fumo": "Consumo não Cíclico",
    "Agricultura (Açúcar, Álcool e Cana)": "Consumo não Cíclico",
    "Emp. Adm. Part. - Agricultura (Açúcar, Álcool e Cana)": "Consumo não Cíclico",
    "Comércio (Atacado e Varejo)": "Consumo Cíclico",
    "Emp. Adm. Part. - Comércio (Atacado e Varejo)": "Consumo Cíclico",
    "Hospedagem e Turismo": "Consumo Cíclico",
    "Emp. Adm. Part. - Hospedagem e Turismo": "Consumo Cíclico",
    "Brinquedos e Lazer": "Consumo Cíclico",
    "Emp. Adm. Part. - Brinquedos e Lazer": "Consumo Cíclico",
    "Têxtil e Vestuário": "Consumo Cíclico",
    "Emp. Adm. Part. - Têxtil e Vestuário": "Consumo Cíclico",
    "Construção Civil, Mat. Constr. e Decoração": "Consumo Cíclico",
    "Emp. Adm. Part. - Const. Civil, Mat. Const. e Decoração": "Consumo Cíclico",
    "Educação": "Consumo Cíclico",
    "Emp. Adm. Part. - Educação": "Consumo Cíclico",
    "Máquinas, Equipamentos, Veículos e Peças": "Bens Industriais",
    "Emp. Adm. Part. - Máqs., Equip., Veíc. e Peças": "Bens Industriais",
    "Serviços Transporte e Logística": "Bens Industriais",
    "Emp. Adm. Part. - Serviços Transporte e Logística": "Bens Industriais",
    "Comércio Exterior": "Bens Industriais",
    "Extração Mineral": "Materiais Básicos",
    "Emp. Adm. Part. - Extração Mineral": "Materiais Básicos",
    "Metalurgia e Siderurgia": "Materiais Básicos",
    "Emp. Adm. Part. - Metalurgia e Siderurgia": "Materiais Básicos",
    "Papel e Celulose": "Materiais Básicos",
    "Emp. Adm. Part. - Papel e Celulose": "Materiais Básicos",
    "Embalagens": "Materiais Básicos",
    "Emp. Adm. Part. - Embalagens": "Materiais Básicos",
    "Petroquímicos e Borracha": "Materiais Básicos",
    "Emp. Adm. Part. - Petroquímicos e Borracha": "Materiais Básicos",
    "Petróleo e Gás": "Petróleo, Gás e Biocombustíveis",
    "Emp. Adm. Part. - Petróleo e Gás": "Petróleo, Gás e Biocombustíveis",
    "Serviços Médicos": "Saúde",
    "Emp. Adm. Part. - Serviços médicos": "Saúde",
    "Farmacêutico e Higiene": "Saúde",
    "Emp. Adm. Part. - Farmacêutico e Higiene": "Saúde",
    "Comunicação e Informática": "Tecnologia da Informação",
    "Emp. Adm. Part. - Comunicação e Informática": "Tecnologia da Informação",
    "Telecomunicações": "Comunicações",
    "Emp. Adm. Part. - Telecomunicações": "Comunicações",
    "Emp. Adm. Participações": "Outros",
    "Emp. Adm. Part. - Sem Setor Principal": "Outros",
    "Gráficas e Editoras": "Outros",
    "Emp. Adm. Part. - Gráficas e Editoras": "Outros",
    "Serviços Diversos": "Outros",
    "Serviços em Geral": "Outros",
    "Pesca": "Outros",
    "Reflorestamento": "Outros",
    "Outras Atividades Industriais": "Outros",
}


def main() -> None:
    data_dir = get_data_dir()
    data_file = data_dir / "emissores_rating.json"
    pulseflat_data = ROOT_DIR.parent / "PulseFlat" / "data"

    if not data_file.exists():
        logger.warning(f"Arquivo {data_file} não encontrado.")
        return

    with data_file.open("r", encoding="utf-8") as f:
        emissores = json.load(f)

    # 1. Load CVM (local cache or external PulseFlat)
    cvm_dict = {}
    for cvm_candidate in [
        data_dir / "cvm_cache" / "cad_cia_aberta.csv",
        pulseflat_data / "cvm_cadastro_companhias_abertas.csv",
    ]:
        if cvm_candidate.exists():
            try:
                sep = ";" if cvm_candidate.name == "cad_cia_aberta.csv" else ","
                enc = "iso-8859-1" if sep == ";" else "utf-8"
                cvm = pd.read_csv(cvm_candidate, sep=sep, encoding=enc, dtype=str)
                col_cnpj = "CNPJ_CIA" if "CNPJ_CIA" in cvm.columns else "cnpj_cia"
                col_setor = "SETOR_ATIV" if "SETOR_ATIV" in cvm.columns else "setor_ativ"
                if col_cnpj in cvm.columns and col_setor in cvm.columns:
                    cvm["cnpj_cia_clean"] = cvm[col_cnpj].str.replace(r"[^0-9]", "", regex=True)
                    cvm_dict = dict(zip(cvm["cnpj_cia_clean"], cvm[col_setor]))
                    break
            except Exception as e:
                logger.warning(f"Erro ao carregar CVM de {cvm_candidate}: {e}")

    # 2. Load B3
    b3_class_dict = {}
    b3_file = pulseflat_data / "b3_classificacao_setorial.csv"
    if b3_file.exists():
        try:
            b3_class = pd.read_csv(b3_file, dtype=str)
            for r in b3_class.to_dict("records"):
                name = str(r.get("nome_empresa", "")).upper().strip()
                b3_class_dict[name] = {
                    "setor": r.get("setor_economico", ""),
                    "subsetor": r.get("subsetor", ""),
                    "segmento": r.get("segmento", ""),
                }
        except Exception as e:
            logger.warning(f"Erro ao carregar B3 de {b3_file}: {e}")

    for e in emissores:
        cnpj = e.get("cnpj", "").replace(".", "").replace("/", "").replace("-", "").zfill(14)
        name_upper = e.get("emissor", "").upper().strip()
        tipo = e.get("tipo_rating", "")

        new_setor = e.get("setor", "")
        new_subsetor = e.get("subsetor", "")
        new_segmento = e.get("segmento", "")

        if name_upper in b3_class_dict and pd.notna(b3_class_dict[name_upper]["setor"]):
            b3_data = b3_class_dict[name_upper]
            new_setor = str(b3_data["setor"])
            new_subsetor = str(b3_data["subsetor"]) if pd.notna(b3_data["subsetor"]) else ""
            new_segmento = str(b3_data["segmento"]) if pd.notna(b3_data["segmento"]) else ""
        elif cnpj in cvm_dict and pd.notna(cvm_dict[cnpj]):
            raw_cvm = cvm_dict[cnpj]
            new_setor = DE_PARA.get(raw_cvm, raw_cvm)
            new_subsetor = raw_cvm if DE_PARA.get(raw_cvm) else ""
        elif not new_setor:
            if any(
                keyword in tipo.upper()
                for keyword in ["FIDC", "CRI", "CRA", "DEBENTURE COLATERALIZADA", "FII", "ABS"]
            ):
                new_setor = "Finanças Estruturadas"
            elif any(
                keyword in tipo.upper()
                for keyword in ["ESTADOS E MUNIC", "FINANÇAS PÚBLICAS", "SOBERANO", "COUNTRY CEILING"]
            ):
                new_setor = "Finanças Públicas"
            elif "FUNDO" in name_upper:
                new_setor = "Fundos de Investimento"

        e["setor"] = new_setor
        e["subsetor"] = new_subsetor
        e["segmento"] = new_segmento

    with data_file.open("w", encoding="utf-8") as f:
        json.dump(emissores, f, ensure_ascii=False, indent=2)

    logger.info("Enriquecimento de setores concluído com sucesso.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()

