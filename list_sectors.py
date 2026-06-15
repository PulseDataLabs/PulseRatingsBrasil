import pandas as pd

cvm = pd.read_csv('../PulseFlat/data/cvm_cadastro_companhias_abertas.csv', dtype=str)
cvm_sectors = cvm['setor_ativ'].dropna().unique()

b3 = pd.read_csv('../PulseFlat/data/b3_classificacao_setorial.csv', dtype=str)
b3_sectors = b3['setor_economico'].dropna().unique()

print("CVM Sectors:", sorted(cvm_sectors))
print("\nB3 Sectors:", sorted(b3_sectors))
