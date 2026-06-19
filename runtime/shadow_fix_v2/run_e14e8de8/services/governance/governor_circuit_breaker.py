from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.governance_models import GovernorDomain
from libs.db.repositories.governor_resilience_repository import GovernorCircuitBreakerRepo

class GovernorCircuitBreaker:
    """Belirli bir governor domain'i için circuit breaker mantığı."""
    
    FAILURE_THRESHOLD = 5
    RECOVERY_WINDOW_MINUTES = 5

    @staticmethod
    async def record_failure(db: AsyncSession, domain: GovernorDomain, reason: str):
        record = await GovernorCircuitBreakerRepo.get_circuit_state(db, domain)
        
        # Basit state machine: CLOSED -> OPEN
        # Gerçek uygulamada in-memory counter kullanılabilir, burada DB bazlı yapıyoruz
        failures = 0
        if record and record.trigger_reason:
            # Önceki hataları say (basitleştirilmiş)
            failures = 1 
            
        if failures >= GovernorCircuitBreaker.FAILURE_THRESHOLD:
            await GovernorCircuitBreakerRepo.upsert_circuit_state(
                db, domain, "OPEN", reason=f"Failure threshold reached: {reason}"
            )
        else:
            await GovernorCircuitBreakerRepo.upsert_circuit_state(
                db, domain, "CLOSED", reason=reason
            )

    @staticmethod
    async def record_success(db: AsyncSession, domain: GovernorDomain):
        await GovernorCircuitBreakerRepo.upsert_circuit_state(
            db, domain, "CLOSED", reason="Success recorded"
        )

    @staticmethod
    async def is_open(db: AsyncSession, domain: GovernorDomain) -> bool:
        record = await GovernorCircuitBreakerRepo.get_circuit_state(db, domain)
        if not record or record.state == "CLOSED":
            return False
            
        if record.state == "OPEN":
            # Recovery window kontrolü
            if record.opened_at:
                elapsed = datetime.now(timezone.utc) - record.opened_at
                if elapsed > timedelta(minutes=GovernorCircuitBreaker.RECOVERY_WINDOW_MINUTES):
                    # Half-open'a geçiş (DB'de state güncelle)
                    await GovernorCircuitBreakerRepo.upsert_circuit_state(db, domain, "HALF_OPEN", reason="Recovery window elapsed")
                    return False # Half-open iken denemeye izin ver
            return True
            
        return False # HALF_OPEN case
