import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / 'data' / 'emissores_rating.json'
PULSEFLAT_DATA = BASE_DIR.parent / 'PulseFlat' / 'data'

DE_PARA = {
    'Bancos': 'Financeiro',
    'Emp. Adm. Part. - Bancos': 'Financeiro',
    'Intermediação Financeira': 'Financeiro',
    'Emp. Adm. Part. - Intermediação Financeira': 'Financeiro',
    'Securitização de Recebíveis': 'Financeiro',
    'Emp. Adm. Part. - Securitização de Recebíveis': 'Financeiro',
    'Factoring': 'Financeiro',
    'Crédito Imobiliário': 'Financeiro',
    'Emp. Adm. Part. - Crédito Imobiliário': 'Financeiro',
    'Arrendamento Mercantil': 'Financeiro',
    'Emp. Adm. Part. - Arrendamento Mercantil': 'Financeiro',
    'Bolsas de Valores/Mercadorias e Futuros': 'Financeiro',
    'Emp. Adm. Part.-Bolsas de Valores/Mercadorias e Futuros': 'Financeiro',
    'Seguradoras e Corretoras': 'Financeiro',
    'Emp. Adm. Part. - Seguradoras e Corretoras': 'Financeiro',
    
    'Energia Elétrica': 'Utilidade Pública',
    'Emp. Adm. Part. - Energia Elétrica': 'Utilidade Pública',
    'Saneamento, Serv. Água e Gás': 'Utilidade Pública',
    'Emp. Adm. Part. - Saneamento, Serv. Água e Gás': 'Utilidade Pública',
    
    'Alimentos': 'Consumo não Cíclico',
    'Emp. Adm. Part. - Alimentos': 'Consumo não Cíclico',
    'Bebidas e Fumo': 'Consumo não Cíclico',
    'Agricultura (Açúcar, Álcool e Cana)': 'Consumo não Cíclico',
    'Emp. Adm. Part. - Agricultura (Açúcar, Álcool e Cana)': 'Consumo não Cíclico',
    
    'Comércio (Atacado e Varejo)': 'Consumo Cíclico',
    'Emp. Adm. Part. - Comércio (Atacado e Varejo)': 'Consumo Cíclico',
    'Hospedagem e Turismo': 'Consumo Cíclico',
    'Emp. Adm. Part. - Hospedagem e Turismo': 'Consumo Cíclico',
    'Brinquedos e Lazer': 'Consumo Cíclico',
    'Emp. Adm. Part. - Brinquedos e Lazer': 'Consumo Cíclico',
    'Têxtil e Vestuário': 'Consumo Cíclico',
    'Emp. Adm. Part. - Têxtil e Vestuário': 'Consumo Cíclico',
    'Construção Civil, Mat. Constr. e Decoração': 'Consumo Cíclico',
    'Emp. Adm. Part. - Const. Civil, Mat. Const. e Decoração': 'Consumo Cíclico',
    'Educação': 'Consumo Cíclico',
    'Emp. Adm. Part. - Educação': 'Consumo Cíclico',
    
    'Máquinas, Equipamentos, Veículos e Peças': 'Bens Industriais',
    'Emp. Adm. Part. - Máqs., Equip., Veíc. e Peças': 'Bens Industriais',
    'Serviços Transporte e Logística': 'Bens Industriais',
    'Emp. Adm. Part. - Serviços Transporte e Logística': 'Bens Industriais',
    'Comércio Exterior': 'Bens Industriais',
    
    'Extração Mineral': 'Materiais Básicos',
    'Emp. Adm. Part. - Extração Mineral': 'Materiais Básicos',
    'Metalurgia e Siderurgia': 'Materiais Básicos',
    'Emp. Adm. Part. - Metalurgia e Siderurgia': 'Materiais Básicos',
    'Papel e Celulose': 'Materiais Básicos',
    'Emp. Adm. Part. - Papel e Celulose': 'Materiais Básicos',
    'Embalagens': 'Materiais Básicos',
    'Emp. Adm. Part. - Embalagens': 'Materiais Básicos',
    'Petroquímicos e Borracha': 'Materiais Básicos',
    'Emp. Adm. Part. - Petroquímicos e Borracha': 'Materiais Básicos',
    
    'Petróleo e Gás': 'Petróleo, Gás e Biocombustíveis',
    'Emp. Adm. Part. - Petróleo e Gás': 'Petróleo, Gás e Biocombustíveis',
    
    'Serviços Médicos': 'Saúde',
    'Emp. Adm. Part. - Serviços médicos': 'Saúde',
    'Farmacêutico e Higiene': 'Saúde',
    'Emp. Adm. Part. - Farmacêutico e Higiene': 'Saúde',
    
    'Comunicação e Informática': 'Tecnologia da Informação',
    'Emp. Adm. Part. - Comunicação e Informática': 'Tecnologia da Informação',
    
    'Telecomunicações': 'Comunicações',
    'Emp. Adm. Part. - Telecomunicações': 'Comunicações',
    
    'Emp. Adm. Participações': 'Outros',
    'Emp. Adm. Part. - Sem Setor Principal': 'Outros',
    'Gráficas e Editoras': 'Outros',
    'Emp. Adm. Part. - Gráficas e Editoras': 'Outros',
    'Serviços Diversos': 'Outros',
    'Serviços em Geral': 'Outros',
    'Pesca': 'Outros',
    'Reflorestamento': 'Outros',
    'Outras Atividades Industriais': 'Outros',
}

with open(DATA_FILE, 'r') as f:
    emissores = json.load(f)

# 1. Load CVM
try:
    cvm = pd.read_csv(PULSEFLAT_DATA / 'cvm_cadastro_companhias_abertas.csv', dtype=str)
    cvm['cnpj_cia_clean'] = cvm['cnpj_cia'].str.replace(r'[^0-9]', '', regex=True)
    cvm_dict = dict(zip(cvm['cnpj_cia_clean'], cvm['setor_ativ']))
except FileNotFoundError:
    cvm_dict = {}

# 2. Load B3
try:
    b3_class = pd.read_csv(PULSEFLAT_DATA / 'b3_classificacao_setorial.csv', dtype=str)
    b3_records = b3_class.to_dict('records')
    b3_class_dict = {}
    for r in b3_records:
        name = str(r.get('nome_empresa', '')).upper().strip()
        b3_class_dict[name] = {
            'setor': r.get('setor_economico', ''),
            'subsetor': r.get('subsetor', ''),
            'segmento': r.get('segmento', '')
        }
except FileNotFoundError:
    b3_class_dict = {}

for e in emissores:
    cnpj = e.get('cnpj', '').replace('.', '').replace('/', '').replace('-', '').zfill(14)
    name_upper = e.get('emissor', '').upper().strip()
    tipo = e.get('tipo_rating', '')

    new_setor = ""
    new_subsetor = ""
    new_segmento = ""

    # B3 has precedence
    if name_upper in b3_class_dict and pd.notna(b3_class_dict[name_upper]['setor']):
        b3_data = b3_class_dict[name_upper]
        new_setor = str(b3_data['setor'])
        new_subsetor = str(b3_data['subsetor']) if pd.notna(b3_data['subsetor']) else ""
        new_segmento = str(b3_data['segmento']) if pd.notna(b3_data['segmento']) else ""
    elif cnpj in cvm_dict and pd.notna(cvm_dict[cnpj]):
        raw_cvm = cvm_dict[cnpj]
        new_setor = DE_PARA.get(raw_cvm, raw_cvm)
        new_subsetor = raw_cvm if DE_PARA.get(raw_cvm) else ""
    else:
        # Inference
        if any(keyword in tipo.upper() for keyword in ['FIDC', 'CRI', 'CRA', 'DEBENTURE COLATERALIZADA', 'FII', 'ABS']):
            new_setor = "Finanças Estruturadas"
        elif any(keyword in tipo.upper() for keyword in ['ESTADOS E MUNIC', 'FINANÇAS PÚBLICAS', 'SOBERANO', 'COUNTRY CEILING']):
            new_setor = "Finanças Públicas"
        elif "FUNDO" in name_upper:
            new_setor = "Fundos de Investimento"

    e['setor'] = new_setor
    e['subsetor'] = new_subsetor
    e['segmento'] = new_segmento

with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(emissores, f, ensure_ascii=False, indent=2)

print("Enrichment complete with DE-PARA.")
