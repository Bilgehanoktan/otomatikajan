import hashlib
from typing import Dict, Any, Tuple
from services.ui_repair.sovereign_identity_registry import SovereignIdentityRegistry

class ServiceIdentityAttestor:
    """Phase 19: Verifies worker and cluster node fingerprints."""
    
    def __init__(self, db_session: AsyncSession):
        self.registry = SovereignIdentityRegistry(db_session)

    async def attest_heartbeat(self, identity_key: str, fingerprint: str) -> Tuple[bool, str]:
        identity = await self.registry.get_identity(identity_key)
        if not identity:
            return False, "UNKNOWN_IDENTITY"
        
        if identity.public_key_fingerprint != fingerprint:
            # Create a critical incident for fingerprint mismatch
            return False, "FINGERPRINT_MISMATCH_CRITICAL"
        
        return True, "ATTESTED"

    @staticmethod
    def generate_fingerprint(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()
