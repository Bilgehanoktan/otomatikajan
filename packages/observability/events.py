import asyncio
from typing import Any, Callable, Dict, List
from observability.logging import get_logger

logger = get_logger("observability.events")

class EventBus:
    """Sistem genelinde asenkron olay iletimi sağlayan basit bir Bus."""
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}")

    async def publish(self, event_type: str, **kwargs):
        """Olayı tüm abonelere dağıtır."""
        if event_type not in self._subscribers:
            return
            
        tasks = []
        for callback in self._subscribers[event_type]:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(callback(event_type, **kwargs))
            else:
                callback(event_type, **kwargs)
                
        if tasks:
            await asyncio.gather(*tasks)

# Global Singleton
event_bus = EventBus()
