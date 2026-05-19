import json

file_path = 'apps/refine_control_plane/src/messages/tr.json'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("JSON is valid.")
    print(f"Keys in dashboard: {list(data.get('dashboard', {}).keys())}")
    if 'aboveThreshold' in data.get('dashboard', {}):
        print(f"dashboard.aboveThreshold: {data['dashboard']['aboveThreshold']}")
    else:
        print("dashboard.aboveThreshold MISSING in object!")
except Exception as e:
    print(f"Error: {e}")
