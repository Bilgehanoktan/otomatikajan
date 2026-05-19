
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from libs.db.models import Base
from services.ui_repair.security_posture_manager import SecurityPostureManager

async def test_manual():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        manager = SecurityPostureManager(session)
        print("Running scan...")
        result = await manager.run_full_scan()
        print(f"Scan result: {result}")
        
        print("Generating certification...")
        cert = await manager.certify_compliance(operator_name="TestAgent")
        print(f"Certification: {cert.cert_id}")

if __name__ == "__main__":
    asyncio.run(test_manual())
