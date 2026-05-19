import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def cleanup_tables():
    url = 'postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/ai_company'
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            # Sadece bu iki tabloyu temizliyoruz
            await conn.execute(text("DROP TABLE IF EXISTS policy_evolution CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS decision_lineage CASCADE"))
        print("CLEANUP_SUCCESS")
    except Exception as e:
        print(f"CLEANUP_ERROR:{e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(cleanup_tables())
