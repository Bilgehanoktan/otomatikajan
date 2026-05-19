import json
import os

en_path = r'e:\ai_company_faz12.1\apps\refine_control_plane\src\messages\en.json'
tr_path = r'e:\ai_company_faz12.1\apps\refine_control_plane\src\messages\tr.json'

with open(en_path, 'r', encoding='utf-8') as f:
    en = json.load(f)

with open(tr_path, 'r', encoding='utf-8') as f:
    tr = json.load(f)

def get_keys(d, prefix=''):
    keys = set()
    for k, v in d.items():
        if isinstance(v, dict):
            keys.update(get_keys(v, prefix + k + '.'))
        else:
            keys.add(prefix + k)
    return keys

en_keys = get_keys(en)
tr_keys = get_keys(tr)

missing_in_tr = en_keys - tr_keys
missing_in_en = tr_keys - en_keys

print(f"Missing in TR: {sorted(list(missing_in_tr))}")
print(f"Missing in EN: {sorted(list(missing_in_en))}")
