import time
import asyncio
import logging
from enum import Enum
from typing import Dict, Optional, Callable, Any
from functools import wraps
from fastapi import HTTPException

logger = logging.getLogger("api.resilience")

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """
    API Katmanı için Hafif Devre Kesici (Circuit Breaker).
    Hata oranlarını takip eder ve eşik aşımında isteği 503 ile reddeder.
    """
    def __init__(
        self, 
        name: str, 
        fail_threshold: int = 5, 
        recovery_timeout: float = 30.0
    ):
        self.name = name
        self.fail_threshold = fail_threshold
        self.recovery_timeout = recovery_timeout
        
        self.state = CircuitState.CLOSED
        self.fail_count = 0
        self.last_failure_time = 0.0

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"[Resilience] {self.name} devresi YARIDAN-KAPALI'ya (CLOSED) döndü.")
            self.state = CircuitState.CLOSED
        self.fail_count = 0

    def record_failure(self):
        self.fail_count += 1
        self.last_failure_time = time.time()
        
        if self.fail_count >= self.fail_threshold:
            if self.state != CircuitState.OPEN:
                logger.error(f"[Resilience] {self.name} devresi AÇILDI (OPEN)! Eşik: {self.fail_threshold}")
            self.state = CircuitState.OPEN

    def is_available(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        
        # Cooldown kontrolü
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"[Resilience] {self.name} devresi YARI-AÇIK (HALF-OPEN) moduna geçti.")
                return True
            return False
        
        return True # HALF_OPEN durumunda teste izin ver

# Global registry for breakers
_breakers: Dict[str, CircuitBreaker] = {}

def get_breaker(name: str, **kwargs) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name, **kwargs)
    return _breakers[name]

def circuit_breaker(name: str, fail_threshold: int = 5, recovery_timeout: float = 30.0):
    """
    FastAPI endpoint'leri için decorator.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = get_breaker(name, fail_threshold=fail_threshold, recovery_timeout=recovery_timeout)
            
            if not breaker.is_available():
                logger.warning(f"[Resilience] {name} isteği reddedildi (Circuit OPEN).")
                raise HTTPException(
                    status_code=503, 
                    detail=f"Servis geçici olarak yoğunluk/hata nedeniyle devredışı ({name}). Lütfen birazdan tekrar deneyin."
                )
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                # 4xx hataları genelde client hatasıdır, devreyi açmamalıyız (opsiyonel)
                if hasattr(e, 'status_code') and 400 <= e.status_code < 500:
                    raise e
                
                breaker.record_failure()
                raise e
        return wrapper
    return decorator
