
import sys
import os

# Add the workspace to sys.path
sys.path.append(r'e:\ai_company_faz12.1')

# Mock environment variables if needed
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost/sovereign_agi"

from services.workflow_api.main import app

for route in app.routes:
    print(f"{route.path} [{','.join(route.methods)}]")
