"""
Sovereign AGI — Phase 27
libs/mesh/event_bridge.py
Real-time Cross-Region State Propagation via Redis Pub/Sub.
"""
import asyncio
import json
from libs.db.session import get_redis_client
from services.observability.logging import get_logger

logger = get_logger("mesh.event_bridge")

class CrossRegionEventBridge:
    def __init__(self):
        self._is_running = False
        self._redis = None
        self._pubsub = None

    async def _init_redis(self):
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis

    async def broadcast_event(self, event_type: str, payload: dict):
        """Sends an event to all other mesh nodes."""
        redis = await self._init_redis()
        if redis:
            try:
                msg = {
                    "type": event_type,
                    "payload": payload,
                    "origin_timestamp": asyncio.get_event_loop().time()
                }
                await redis.publish("mesh:global:events", json.dumps(msg))
                return True
            except Exception as e:
                logger.error(f"Broadcast failed: {e}")
        return False

    async def start_listening(self, callback):
        """Listens for global mesh events and triggers local updates."""
        self._is_running = True
        redis = await self._init_redis()
        if not redis:
            logger.warning("EventBridge: Redis unavailable, staying in silent mode.")
            return

        pubsub = redis.pubsub()
        await pubsub.subscribe("mesh:global:events", "mesh:state:updates")
        
        logger.info("EventBridge: Listening for Global Mesh Events...")
        
        while self._is_running:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    data = json.loads(message['data'])
                    await callback(data)
            except Exception as e:
                logger.error(f"EventBridge listen error: {e}")
                await asyncio.sleep(2)
            await asyncio.sleep(0.01)

event_bridge = CrossRegionEventBridge()
