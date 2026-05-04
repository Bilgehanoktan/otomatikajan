import requests

print('--- MESH STATUS TEST ---')
mesh_res = requests.get('http://localhost:8000/api/v1/mesh/status')
if mesh_res.status_code == 200:
    data = mesh_res.json()
    print(f"Global Status: {data.get('global_status')}")
    print(f"Quorum Maintained: {data.get('quorum_maintained')}")
    print(f"Active Regions: {data.get('region_count', {}).get('healthy')}/{data.get('region_count', {}).get('total')}")
else:
    print(f"Mesh Error: {mesh_res.status_code}")

print('\n--- AUTH & APPROVALS TEST ---')
login_res = requests.post('http://localhost:8000/api/v1/auth/login/', json={'email':'admin@sovereign.agi','password':'admin1234'})
if login_res.status_code == 200:
    token = login_res.json().get('access_token')
    print('Login Successful. Token obtained.')
    
    app_res = requests.get('http://localhost:8000/api/v1/governance/approvals?status=pending', headers={'Authorization': f'Bearer {token}'})
    if app_res.status_code == 200:
        print(f"Approvals API: HTTP 200 OK. Total pending: {len(app_res.json())}")
    else:
        print(f"Approvals API Error: HTTP {app_res.status_code}")
else:
    print(f"Login Failed: HTTP {login_res.status_code}")
