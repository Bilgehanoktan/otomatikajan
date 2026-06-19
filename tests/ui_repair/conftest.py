import asyncio
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from libs.db.models import Base
from libs.db.session import get_db
from services.auth.jwt_auth import get_current_identity


@pytest.fixture(autouse=True)
def _reset_asyncio_state_after_ui_repair_test():
    yield
    asyncio.set_event_loop_policy(asyncio.get_event_loop_policy())
    try:
        asyncio.set_event_loop(None)
    except Exception:
        pass

@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    from apps.public_api.main import app
    
    # Override get_db to use our test session
    async def override_get_db():
        yield db_session

    async def override_identity():
        return {
            "id": uuid.uuid4(),
            "type": "operator",
            "role": "OPERATOR",
            "email": "operator@test.local",
            "name": "Test Operator",
        }
        
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_identity] = override_identity
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()
