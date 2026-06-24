"""
Alembic env.py — async SQLAlchemy ile production migration
"""
import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

try:
    from dotenv import load_dotenv
    if os.path.exists(".env.local"):
        load_dotenv(".env.local", override=False)
    elif os.path.exists(".env"):
        load_dotenv(".env")
except ImportError:
    pass

from libs.db.models.core_models import Base
import libs.db.models

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(element, compiler, **kw):
    return "CHAR(36)"



config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# DATABASE_URL env'den/config'den al (alembic.ini override eder)
try:
    from libs.config import DATABASE_URL as db_url
except ImportError:
    db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

if db_url:
    # Ensure correct async prefix for alembic asyncpg engine
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    elif db_url.startswith("sqlite://"):
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    # Cross-Dialect Compatibility (V2)
    def process_revision_directives(context, revision, directives):
        if config.get_main_option("sqlalchemy.url").startswith("sqlite"):
            # SQLite specific fixes if needed during autogenerate
            pass

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Phase 12.1: JSONB and UUID mapping for SQLite
        render_as_batch=True if connection.dialect.name == "sqlite" else False,
        process_revision_directives=process_revision_directives
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
