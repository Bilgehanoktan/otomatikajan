from typing import List, Dict

class MetaGovernorConfig:
    """
    Federated Governance için öncelik ve kısıt ayarları.
    """
    
    # Domain öncelik sırası (Daha yüksek risk/güvenlik odağı olan üstte)
    DOMAIN_PRIORITY = [
        "POLICY",
        "INCIDENT",
        "REPAIR",
        "WORKFLOW",
        "APPROVAL"
    ]
    
    # Veto yetkisi olan domain'ler
    VETO_DOMAINS = ["POLICY", "INCIDENT"]
    
    # Otomatik eskalasyon kuralları
    ESCALATION_RULES = {
        "CRITICAL_INCIDENT": "REQUIRES_PRIME_REVIEW",
        "CONSTITUTIONAL_CHANGE": "REQUIRES_QUORUM",
        "STALE_FAILED_WORKFLOW": "ARCHIVE_STALE"
    }

    @classmethod
    def get_priority(cls, domain_name: str) -> int:
        try:
            return cls.DOMAIN_PRIORITY.index(domain_name)
        except ValueError:
            return 99
