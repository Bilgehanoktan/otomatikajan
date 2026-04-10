import os
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Force LOCAL database URL
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_company"

# Now import and run the test
from tools.maintenance.auto_test import run_tests

if __name__ == "__main__":
    asyncio.run(run_tests())
