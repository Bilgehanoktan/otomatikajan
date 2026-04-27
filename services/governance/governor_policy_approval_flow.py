import logging
from libs.db.models.governance_models import GovernorPolicyEvolutionRecord, PolicyEvolutionType

logger = logging.getLogger(__name__)

class GovernorPolicyApprovalFlow:
    @staticmethod
    def determine_approval_path(evolution: GovernorPolicyEvolutionRecord) -> str:
        """Politika değişikliği için gereken onay seviyesini belirler."""
        
        # 1. Yüksek Riskli: Veto önceliği veya Çakışma Çözüm mantığı değişimleri -> QUORUM
        if evolution.evolution_type in [
            PolicyEvolutionType.VETO_PRIORITY_CHANGE, 
            PolicyEvolutionType.CONFLICT_RESOLUTION_CHANGE
        ]:
            return "QUORUM"
            
        # 2. Orta Riskli: Arşiv/Replay/Eskalasyon politikaları -> PRIME
        if evolution.evolution_type in [
            PolicyEvolutionType.ESCALATION_POLICY_CHANGE,
            PolicyEvolutionType.ARCHIVE_POLICY_CHANGE,
            PolicyEvolutionType.REPLAY_POLICY_CHANGE
        ]:
            return "PRIME"
            
        # 3. Düşük Riskli: Genel kural tweak'leri -> PRIME (veya otonom eğer confidence yüksekse)
        if evolution.confidence_score > 0.95:
            return "AUTONOMOUS_ADVISORY" # Hala onay ister ama öneri güçlüdür
            
        return "PRIME"

    @staticmethod
    def requires_quorum(evolution: GovernorPolicyEvolutionRecord) -> bool:
        return GovernorPolicyApprovalFlow.determine_approval_path(evolution) == "QUORUM"

    @staticmethod
    def requires_prime(evolution: GovernorPolicyEvolutionRecord) -> bool:
        return GovernorPolicyApprovalFlow.determine_approval_path(evolution) == "PRIME"
