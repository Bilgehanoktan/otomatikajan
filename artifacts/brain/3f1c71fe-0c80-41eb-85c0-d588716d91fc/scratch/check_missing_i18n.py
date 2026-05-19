import json
import os

en_path = r'e:\ai_company_faz12.1\apps\refine_control_plane\src\messages\en.json'
tr_path = r'e:\ai_company_faz12.1\apps\refine_control_plane\src\messages\tr.json'

def get_keys(d, prefix=''):
    keys = set()
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        keys.add(full_key)
        if isinstance(v, dict):
            keys.update(get_keys(v, full_key))
    return keys

with open(en_path, 'r', encoding='utf-8') as f:
    en_data = json.load(f)

with open(tr_path, 'r', encoding='utf-8') as f:
    tr_data = json.load(f)

en_keys = get_keys(en_data)
tr_keys = get_keys(tr_data)

missing_in_tr = en_keys - tr_keys
print(f"Missing in TR: {len(missing_in_tr)}")
for k in sorted(missing_in_tr):
    print(f"  - {k}")
