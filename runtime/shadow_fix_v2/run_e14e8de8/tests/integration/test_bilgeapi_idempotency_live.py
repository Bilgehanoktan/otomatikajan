import pytest
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import NullPool
from libs.db.base import Base
from apps.bilgeapi.models.database import BilgeAPIBridgeMappingModel
from services.integrations.bilgeapi_bridge import BilgeAPIBridge
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.mark.asyncio
async def test_bridge_mapping_unique_constraint_sqlite():
    """Verify that uq_bilgeapi_bridge_source unique constraint prevents duplicate mappings in DB."""
    db_name = f"memdb_unique_{uuid.uuid4().hex}"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///file:{db_name}?mode=memory&cache=shared",
        connect_args={"uri": True},
        poolclass=NullPool,
        echo=False
    )
    async with engine.connect() as keep_alive:
        await keep_alive.run_sync(Base.metadata.create_all)
        
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Try inserting duplicate records
        async with async_session() as session1:
            mapping1 = BilgeAPIBridgeMappingModel(
                id="map_1",
                source_type="CONCURRENT_TEST",
                source_id="id_123",
                bilgeapi_finding_id="fnd_1",
                status="FORWARDED"
            )
            session1.add(mapping1)
            await session1.commit()

        async with async_session() as session2:
            mapping2 = BilgeAPIBridgeMappingModel(
                id="map_2",
                source_type="CONCURRENT_TEST",
                source_id="id_123",
                bilgeapi_finding_id="fnd_2",
                status="FORWARDED"
            )
            session2.add(mapping2)
            with pytest.raises(IntegrityError):
                await session2.commit()

    await engine.dispose()


@pytest.mark.asyncio
async def test_bridge_forward_concurrent_intake():
    """Verify concurrent signal intake calls on bridge."""
    db_name = f"memdb_concurrent_{uuid.uuid4().hex}"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///file:{db_name}?mode=memory&cache=shared",
        connect_args={"uri": True},
        poolclass=NullPool,
        echo=False
    )
    async with engine.connect() as keep_alive:
        await keep_alive.run_sync(Base.metadata.create_all)
        
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "finding_id": "fnd_concurrent_abc",
            "created": True,
            "deduped": False
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            async def run_forward(session_factory):
                async with session_factory() as session:
                    bridge = BilgeAPIBridge(db_session=session)
                    try:
                        return await bridge.forward_finding_intake(
                            source_type="TASKFLOW_CONCURRENT",
                            source_id="run_concurrent_123",
                            title="Concurrent Title",
                            description="Description",
                            severity="HIGH"
                        )
                    except Exception as e:
                        await session.rollback()
                        return e

            # Call forward concurrently in separate sessions
            results = await asyncio.gather(
                run_forward(async_session),
                run_forward(async_session)
            )
            
            # At least one must succeed and return the status dict
            successes = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
            assert len(successes) >= 1
            
            # Verify exactly one mapping exists in the DB
            async with async_session() as session:
                stmt = select(BilgeAPIBridgeMappingModel).where(
                    BilgeAPIBridgeMappingModel.source_type == "TASKFLOW_CONCURRENT",
                    BilgeAPIBridgeMappingModel.source_id == "run_concurrent_123"
                )
                mappings = (await session.execute(stmt)).scalars().all()
                assert len(mappings) == 1

    await engine.dispose()
