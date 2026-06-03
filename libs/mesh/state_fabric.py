"""
Sovereign AGI — Phase 27
libs/mesh/state_fabric.py
Hybrid Distributed Fabric: Supports Redis for Cloud and SQLite for Local Shared State.
Ensures R-03 "Real Backend Activation" in all environments.
"""
import json
import asyncio
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Import DB session for SQLite fallback logic
from libs.db.session import get_redis_client, get_db, get_db_ctx
from sqlalchemy import text
from services.observability.logging import get_logger

logger = get_logger("mesh.state_fabric")

class GlobalStateFabric:
    def __init__(self):
        self._redis = None
        self._local_cache = {}
        self._initialized_db = False

    async def _init_redis(self):
        try:
            if self._redis is None:
                self._redis = await get_redis_client()
            return self._redis
        except Exception:
            return None

    async def _ensure_db_table(self):
        """Ensures the mesh_fabric table exists in SQLite for shared local state."""
        if self._initialized_db: return
        async with get_db_ctx() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS mesh_fabric (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME
                )
            """))
            await session.commit()
        self._initialized_db = True

    async def put_state(self, key: str, value: Any):
        """Puts state into the distributed fabric (Redis or Shared SQLite)."""
        redis = await self._init_redis()
        json_val = json.dumps(value)
        
        if redis:
            try:
                await redis.set(f"mesh:fabric:{key}", json_val)
                return True
            except Exception as e:
                logger.debug(f"Fabric: Redis put failed, falling back to SQLite: {e}")

        # SQLite Shared State Fallback (R-03 Durable Activation)
        try:
            await self._ensure_db_table()
            async with get_db_ctx() as session:
                # SRE: Ensure we are in a transaction explicitly for SQLite safety
                await session.execute(text("""
                    INSERT INTO mesh_fabric (key, value, updated_at)
                    VALUES (:key, :value, :updated_at)
                    ON CONFLICT(key) DO UPDATE SET 
                        value = excluded.value,
                        updated_at = excluded.updated_at
                """), {"key": key, "value": json_val, "updated_at": datetime.now(timezone.utc)})
                await session.commit()
            logger.debug(f"Fabric: State '{key}' synced to Shared SQLite (R-03 Active)")
            return True
        except Exception as e:
            # If even SQLite fails, use local in-memory fallback
            logger.warning(f"Fabric: SQLite put failed, using in-memory local fallback: {e}")
            self._local_cache[key] = value
            return False

    async def get_state(self, key: str) -> Optional[Any]:
        """Gets state from the distributed fabric."""
        redis = await self._init_redis()
        if redis:
            try:
                val = await redis.get(f"mesh:fabric:{key}")
                if val: return json.loads(val)
            except Exception:
                pass

        # SQLite Shared State Fallback
        try:
            await self._ensure_db_table()
            async with get_db_ctx() as session:
                result = await session.execute(
                    text("SELECT value FROM mesh_fabric WHERE key = :key"), {"key": key}
                )
                row = result.fetchone()
                if row: return json.loads(row[0])
        except Exception:
            pass

        return self._local_cache.get(key)

    async def put_region_state(self, region_id: str, state: Dict[str, Any]):
        return await self.put_state(f"region:{region_id}", state)

    async def get_mesh_view(self) -> Dict[str, Any]:
        """Returns the full mesh state across all known regions."""
        redis = await self._init_redis()
        mesh_view = {}
        
        if redis:
            try:
                keys = await redis.keys("mesh:fabric:region:*")
                for k in keys:
                    region_id = k.split(":")[-1]
                    val = await redis.get(k)
                    if val: mesh_view[region_id] = json.loads(val)
                if mesh_view: return mesh_view
            except Exception:
                pass

        # SQLite View Fallback
        try:
            await self._ensure_db_table()
            async with get_db_ctx() as session:
                result = await session.execute(
                    text("SELECT key, value FROM mesh_fabric WHERE key LIKE 'region:%'")
                )
                for row in result:
                    region_id = row[0].split(":")[-1]
                    mesh_view[region_id] = json.loads(row[1])
        except Exception:
            pass
            
        return mesh_view

    # --- R-03 Distributed Locking (Consensus Support) ---
    async def acquire_global_lock(self, lock_id: str, owner_id: str = "default", timeout: int = 30) -> bool:
        """Acquires a distributed lock for leader election or cross-region coordination."""
        redis = await self._init_redis()
        if redis:
            try:
                # Redis-NX: Atomic lock acquisition
                acquired = await redis.set(f"mesh:lock:{lock_id}", owner_id, ex=timeout, nx=True)
                return bool(acquired)
            except Exception:
                pass

        # SQLite Lock Fallback (R-03 Durable Consensus)
        try:
            await self._ensure_db_table()
            async with get_db_ctx() as session:
                # 1. Clear expired locks
                await session.execute(text("""
                    DELETE FROM mesh_fabric WHERE key = :lock_key AND updated_at < :expiry
                """), {"lock_key": f"lock:{lock_id}", "expiry": datetime.now(timezone.utc)})
                
                # 2. Try to insert lock
                try:
                    expiry_time = datetime.now(timezone.utc).timestamp() + timeout
                    await session.execute(text("""
                        INSERT INTO mesh_fabric (key, value, updated_at)
                        VALUES (:key, :value, :updated_at)
                    """), {
                        "key": f"lock:{lock_id}", 
                        "value": owner_id, 
                        "updated_at": datetime.fromtimestamp(expiry_time)
                    })
                    await session.commit()
                    return True
                except Exception:
                    # Key already exists -> Lock is held by someone else
                    return False
        except Exception as e:
            logger.error(f"Fabric: Lock acquisition error: {e}")
            return False

    async def release_global_lock(self, lock_id: str, owner_id: str):
        """Releases a distributed lock safety (only if we own it)."""
        redis = await self._init_redis()
        if redis:
            try:
                current_owner = await redis.get(f"mesh:lock:{lock_id}")
                if current_owner == owner_id:
                    await redis.delete(f"mesh:lock:{lock_id}")
                return
            except Exception:
                pass

        # SQLite Lock Release
        try:
            async with get_db_ctx() as session:
                await session.execute(text("""
                    DELETE FROM mesh_fabric WHERE key = :lock_key AND value = :owner
                """), {"lock_key": f"lock:{lock_id}", "owner": owner_id})
                await session.commit()
        except Exception:
            pass

    # Project Snapshots for Fleet Visibility
    async def put_project_snapshot(self, project_id: str, snapshot: Dict[str, Any]):
        return await self.put_state(f"project:{project_id}", snapshot)

    async def get_project_snapshot(self, project_id: str) -> Optional[Dict[str, Any]]:
        return await self.get_state(f"project:{project_id}")

state_fabric = GlobalStateFabric()
