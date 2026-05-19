import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect

async def inspect_schema():
    url = 'postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/ai_company'
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            def get_cols(sync_conn):
                insp = inspect(sync_conn)
                return {
                    "decision_lineage": insp.get_columns("decision_lineage"),
                    "policy_evolution": insp.get_columns("policy_evolution")
                }
            
            data = await conn.run_sync(get_cols)
            for table, cols in data.items():
                col_names = [c["name"] for c in cols]
                print(f"TABLE:{table} | COLS:{','.join(col_names)}")
    except Exception as e:
        print(f"ERROR:{e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(inspect_schema())
