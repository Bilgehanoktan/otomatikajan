import asyncio
from sqlalchemy import text
from libs.db.session import get_db, get_db_ctx

async def apply_migration():
    sql_path = "e:/ai_company_faz12.1/libs/db/migrations/manual/migration_phase30.sql"
    print(f"Reading migration from {sql_path}...")
    
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split by double semicolon or handle blocks if necessary
    # Since it's a small script, we execute it in a transaction
    async with get_db_ctx() as db:
        print("Executing migration...")
        # Note: SQLAlchemy execute(text(...)) handles parameter binding, 
        # but for schema changes we can wrap the whole content.
        # PostgreSQL DO blocks and INDEX creations work fine.
        await db.execute(text(sql_content))
        await db.commit()
    
    print("Migration applied successfully.")

if __name__ == "__main__":
    asyncio.run(apply_migration())
