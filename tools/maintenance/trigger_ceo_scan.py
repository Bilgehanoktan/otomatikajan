import asyncio
import logging
import sys
import os

# PYTHONPATH set edilmeli
sys.path.append(os.getcwd())

from packages.orchestration.ceo.engine import get_ceo_engine
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.persistence.session import init_db

async def main():
    print("CEO Scan tetikleniyor...")
    # DB tablolarının hazır olduğundan emin olalım
    await init_db()
    
    ceo = get_ceo_engine()
    await ceo.run_scan()
    print("CEO Scan tamamlandı.")

if __name__ == "__main__":
    asyncio.run(main())
