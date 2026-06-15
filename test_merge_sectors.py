import json
import pandas as pd

with open('data/emissores_rating.json', 'r') as f:
    emissores = json.load(f)

# Load CVM Cias Abertas
cvm = pd.read_csv('../PulseFlat/data/cvm_cadastro_companhias_abertas.csv', dtype=str)
cvm['cnpj_cia_clean'] = cvm['cnpj_cia'].str.replace(r'[^0-9]', '', regex=True)
cvm_dict = dict(zip(cvm['cnpj_cia_clean'], cvm['setor_ativ']))

# Load B3 Classificação
# We need to map CNPJ to B3 Sector.
# But B3 Classificacao only has nome_empresa and codigo.
# b3_isin_emissores has CNPJ and nome_emissor.
b3_emissores = pd.read_csv('../PulseFlat/data/b3_isin_emissores.csv', dtype=str)
b3_emissores['cnpj_clean'] = b3_emissores['cnpj_emissor'].str.zfill(14)
# Try to match B3 classificacao by exact name or ticker?
b3_class = pd.read_csv('../PulseFlat/data/b3_classificacao_setorial.csv', dtype=str)
b3_class_dict = dict(zip(b3_class['nome_empresa'].str.upper(), b3_class['setor_economico']))

matched_cvm = 0
matched_b3 = 0
total_emissores = len(set(e['cnpj'] for e in emissores if e.get('cnpj')))

for e in emissores:
    cnpj = e.get('cnpj', '').replace('.', '').replace('/', '').replace('-', '').zfill(14)
    if cnpj in cvm_dict:
        e['setor_cvm'] = cvm_dict[cnpj]
        matched_cvm += 1
    # Try B3 by name
    name_upper = e.get('emissor', '').upper()
    if name_upper in b3_class_dict:
        e['setor_b3'] = b3_class_dict[name_upper]
        matched_b3 += 1

print(f"Total Unique CNPJs in Ratings: {total_emissores}")
print(f"Matched by CVM: {matched_cvm} ratings (not unique)")
print(f"Matched by B3 name: {matched_b3} ratings (not unique)")
