
import asyncio
from libs.db.session import get_db, get_db_ctx
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_fix")

async def fix_schema():
    async with get_db_ctx() as session:
        logger.info("Dropping table multi_party_signoffs to force schema update...")
        await session.execute(text("DROP TABLE IF EXISTS multi_party_signoffs CASCADE;"))
        await session.commit()
    logger.info("Table dropped successfully.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
