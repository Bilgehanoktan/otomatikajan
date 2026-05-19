import json

def get_keys(d, prefix=''):
    keys = set()
    for k, v in d.items():
        new_key = f"{prefix}.{k}" if prefix else k
        keys.add(new_key)
        if isinstance(v, dict):
            keys.update(get_keys(v, new_key))
    return keys

try:
    with open('apps/refine_control_plane/src/messages/en.json', 'r', encoding='utf-8') as f:
        en = json.load(f)
    with open('apps/refine_control_plane/src/messages/tr.json', 'r', encoding='utf-8') as f:
        tr = json.load(f)

    en_keys = get_keys(en)
    tr_keys = get_keys(tr)

    missing_in_tr = en_keys - tr_keys
    missing_in_en = tr_keys - en_keys

    print("Missing in tr.json:")
    for k in sorted(missing_in_tr):
        print(f"  - {k}")

    print("\nMissing in en.json:")
    for k in sorted(missing_in_en):
        print(f"  - {k}")

except Exception as e:
    print(f"Error: {e}")
