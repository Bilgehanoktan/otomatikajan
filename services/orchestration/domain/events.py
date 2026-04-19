"""
Domain Event Bus
Sistemdeki tüm olaylar bu modülden geçer.
Yayıncılar (orchestrator, heal_engine) -> EventBus -> Aboneler (ws, webhook, log, db)

Olaylar:
  project.started      project.completed    project.failed
  subtask.started      subtask.done         subtask.failed        subtask.recovered
  provider.degraded    provider.recovered   provider.circuit_open  provider.quarantined
  heal.warning         heal.critical        heal.action           heal.resolved
  system.budget_warn   system.cascade_fail
"""

import asyncio
import json
import os
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Awaitable, Any, Optional, Union

EVENT_BUS_MODE = os.getenv("EVENT_BUS_MODE", "redis").lower()

@dataclass
class DomainEvent:
    type:      str
    payload:   dict
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

Handler = Callable[[DomainEvent], Awaitable[None]]

class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Handler]] = {}
        self._wildcard: list[Handler] = []
        self._history:  deque[DomainEvent] = deque(maxlen=500)
        self._redis_conn: Any = None
        self._channel = "system_events"
        self._listen_task: Optional[asyncio.Task] = None
        self.instance_id = str(uuid.uuid4())  # Deduplikasyon için benzersiz kimlik

    def on(self, event_type: str, handler: Handler):
        self._handlers.setdefault(event_type, []).append(handler)

    def on_any(self, handler: Handler):
        self._wildcard.append(handler)

    async def _get_redis(self) -> Any:
        # Faz 12.2: Merkezi Redis istemcisini kullan (SRE Hardening)
        if EVENT_BUS_MODE == "local":
            return None

        if self._redis_conn is not None:
            return self._redis_conn
            
        try:
            from libs.db.session import get_redis_client
            self._redis_conn = await get_redis_client()
            
            if self._redis_conn is not None:
                # Listener başlat
                if self._listen_task is None:
                    self._listen_task = asyncio.create_task(self._listen_redis())
            return self._redis_conn
        except Exception as e:
            from services.observability.logging import get_logger
            get_logger("events").warning(f"⚠️  EventBus Redis bağlantı hatası: {e}")
            return None


    async def _listen_redis(self):
        """Redis'ten gelen olayları dinle ve yerel handler'ları tetikle."""
        try:
            r = await self._get_redis()
            if not r: return
            
            pubsub = r.pubsub()
            await pubsub.subscribe(self._channel)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        
                        # Eğer olay bu instance tarafından gönderildiyse, yerel handler'ları tekrar tetikleme
                        if data.get("sender_id") == self.instance_id:
                            continue

                        event = DomainEvent(
                            type=data["type"],
                            payload=data["payload"],
                            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat())
                        )
                        # Yerel handler'ları tetikle (ama tekrar Redis'e basma!)
                        await self._emit_local(event)
                    except Exception as e:
                        print(f"⚠️  EventBus Redis mesaj işleme hatası: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"⚠️  EventBus Redis dinleme hatası: {e}")

    async def emit(self, event_type: str, **payload):
        event = DomainEvent(type=event_type, payload=payload)
        
        # 1. Redis'e bas (Dağıtık sistem için)
        r = await self._get_redis()
        if r:
            try:
                await r.publish(self._channel, json.dumps({
                    "type": event.type,
                    "payload": event.payload,
                    "timestamp": event.timestamp,
                    "sender_id": self.instance_id  # Gönderen kimliğini ekle
                }))
            except Exception as e:
                print(f"[WARN] EventBus Redis publish hatasi: {e}")

        # 2. Yerel handler'ları tetikle (Hız için)
        await self._emit_local(event)

    async def _emit_local(self, event: DomainEvent):
        # Geçmişe ekle
        if event not in self._history:
            self._history.append(event)

        handlers = self._handlers.get(event.type, []) + self._wildcard
        if handlers:
            await asyncio.gather(
                *[self._safe_call(h, event) for h in handlers],
                return_exceptions=True,
            )

    async def _safe_call(self, handler: Handler, event: DomainEvent):
        try:
            await handler(event)
        except Exception as e:
            from services.observability.logging import get_logger
            get_logger("events").warning(
                f"⚠️  EventBus handler hatası [{event.type}] ({handler.__name__ if hasattr(handler, '__name__') else 'unknown'}): {e}"
            )

    def recent(self, n: int = 50) -> list[dict]:
        events = list(self._history)
        return [{"event": e.type, "type": e.type, "timestamp": e.timestamp, **e.payload}
                for e in events[-n:]]

    async def shutdown(self):
        """EventBus kaynaklarını temizle."""
        if self._listen_task is not None:
            self._listen_task.cancel()
            try:
                # Type hint for Pyre (satisfy awaitable check)
                awaitable_task: Any = self._listen_task
                await awaitable_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        if self._redis_conn:
            try:
                await self._redis_conn.close()
            except Exception:
                pass
            self._redis_conn = None

event_bus = EventBus()
