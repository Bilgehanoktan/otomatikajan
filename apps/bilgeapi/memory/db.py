import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from apps.bilgeapi.memory.models import WorkspaceBase

# Thread/Process safe engine cache to prevent creating multiple engines for the same database path
_engines = {}

def get_workspace_db_url(workspace_dir: Path) -> str:
    db_path = workspace_dir / "memory" / "bilgeapi.db"
    # Ensure parent directories exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path = os.path.abspath(db_path).replace('\\', '/')
    return f"sqlite+aiosqlite:///{abs_path}?timeout=60"

def get_workspace_engine(workspace_dir: Path):
    db_url = get_workspace_db_url(workspace_dir)
    if db_url not in _engines:
        engine = create_async_engine(
            db_url,
            connect_args={"timeout": 60}
        )

        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=60000")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        _engines[db_url] = engine

    return _engines[db_url]

async def init_workspace_db(workspace_dir: Path):
    """
    Initializes the database schema (DDL) inside the designated workspace directory.
    """
    engine = get_workspace_engine(workspace_dir)
    for attempt in range(3):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(WorkspaceBase.metadata.create_all)
            return
        except OperationalError as exc:
            if "already exists" not in str(exc).lower() or attempt == 2:
                raise
            await asyncio.sleep(0.1 * (attempt + 1))

@asynccontextmanager
async def get_workspace_db_session(workspace_dir: Path):
    """
    Async context manager providing a session bound to the workspace SQLite database.
    """
    engine = get_workspace_engine(workspace_dir)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
