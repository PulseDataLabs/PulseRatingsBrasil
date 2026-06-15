import json
with open('data/emissores_rating.json', 'r') as f:
    emissores = json.load(f)

empty = [e for e in emissores if e.get('setor') == ""]
from collections import Counter
print("Empty sector count:", len(empty))
print("By tipo_rating:", Counter(e.get('tipo_rating', '') for e in empty))
