from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, TypeVar, Awaitable
import asyncio
import functools
from services.observability.logging import get_logger

logger = get_logger("integrations.base")

T = TypeVar("T")

def async_retry(max_retries: int = 3, backoff: float = 2.0):
    """Simple async retry decorator with exponential backoff."""
    def decorator(func: Callable[..., Awaitable[T]]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_err = None
            for i in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    wait = backoff * (2 ** i)
                    logger.warning(f"Retry {i+1}/{max_retries} for {func.__name__} after {wait}s: {e}")
                    await asyncio.sleep(wait)
            logger.error(f"Failed {func.__name__} after {max_retries} attempts: {last_err}")
            raise last_err
        return wrapper
    return decorator

class BaseIntegrationTool(ABC):
    """
    Base class for all Sovereign AGI integration adapters.
    Ensures consistent logging, timeout, and retry behavior.
    """
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.logger = get_logger(f"integrations.{tool_name}")

    @abstractmethod
    async def call(self, action: str, **kwargs) -> Any:
        """Main entry point for tool actions."""
        pass
