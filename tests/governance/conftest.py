import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from libs.db.base import Base

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Sets up a temporary SQLite database for governance tests.
    """
    # Use a specific test DB file in the scratch/test directory or in memory
    test_db_url = "sqlite:///governance_test.db"
    
    import libs.config
    old_url = libs.config.DATABASE_URL
    libs.config.DATABASE_URL = "sqlite+aiosqlite:///governance_test.db"
    
    from sqlalchemy.pool import NullPool
    from sqlalchemy import text
    engine = create_engine(test_db_url, poolclass=NullPool)
    
    # Enable WAL mode synchronously on the database file
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA synchronous=NORMAL"))
    
    # Create all tables (including the new governance ones)
    from libs.db.models import governance_models, core_models, repair_models, learning_models
    Base.metadata.create_all(engine)
    
    # Dispose immediately to release connection locks on the file
    engine.dispose()
    
    yield engine
    
    # Cleanup
    engine.dispose()
    
    try:
        if os.path.exists("governance_test.db"):
            os.remove("governance_test.db")
    except Exception as e:
        print(f"Warning: Could not remove test database: {e}")
    
    libs.config.DATABASE_URL = old_url

@pytest.fixture
def db_session(setup_test_db):
    """
    Provides a clean sync session for each test.
    """
    engine = setup_test_db
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
