from typing import Tuple
from libs.db.models.governance_models import GovernorCaseRecord

class ApprovalGovernorExecutionPolicy:
    """
    Governor'ın kararlarını veya operatörün manuel override işlemlerini 
    denetleyen Execution Safety Layer.
    """
    
    PROTECTED_RISK_CLASSES = ["HIGH", "CRITICAL"]
    PROTECTED_PENDING_REASONS = ["SAFETY_LOCK", "MISSING_CONTEXT"]

    def can_auto_approve(self, case: GovernorCaseRecord) -> Tuple[bool, str]:
        if case.risk_class in self.PROTECTED_RISK_CLASSES:
            return False, "EXECUTION_BLOCKED_BY_POLICY: Yüksek riskli işlemler otonom onaylanamaz."
        if case.pending_reason in self.PROTECTED_PENDING_REASONS:
            return False, "EXECUTION_BLOCKED_BY_POLICY: Güvenlik kilidi olan işlemler otonom onaylanamaz."
        if case.requires_prime or case.requires_quorum:
            return False, "REQUIRES_OPERATOR_SCOPE: İşlem Prime veya Quorum onayı gerektiriyor."
        return True, "OK"

    def can_auto_replay(self, case: GovernorCaseRecord) -> Tuple[bool, str]:
        if case.risk_class == "CRITICAL":
            return False, "EXECUTION_BLOCKED_BY_POLICY: Kritik risk seviyesindeki işlemler otonom replay edilemez."
        if case.pending_reason == "SAFETY_LOCK":
            return False, "EXECUTION_BLOCKED_BY_POLICY: Güvenlik kilidi (Safety Lock) replay edilerek atlatılamaz."
        if case.requires_quorum:
            return False, "REQUIRES_OPERATOR_SCOPE: Quorum gerektiren işlemler otonom replay edilemez."
        return True, "OK"

    def can_archive(self, case: GovernorCaseRecord) -> Tuple[bool, str]:
        # Arşivleme genellikle zararsızdır ama Prime onayı bekleyen bir şeyi Governor otonom arşivlememeli,
        # sadece Prime veya Human karar vermelidir, exception: çok eskimişse (stale).
        if case.requires_prime and case.stale_seconds < 86400 * 3:
            # 3 günden önce eskalasyonlar arşivlenemez
            return False, "EXECUTION_BLOCKED_BY_POLICY: Eskale edilmiş işlem yeterince eskimeden (3 gün) otonom arşivlenemez."
        return True, "OK"

    def can_override(self, case: GovernorCaseRecord, operator_role: str, action: str, justification: str) -> Tuple[bool, str]:
        if not operator_role:
            return False, "MISSING_OPERATOR_IDENTITY: Override işlemi kimlik gerektirir."
        
        if len(justification or "") < 20:
            return False, "INVALID_JUSTIFICATION: Override işlemi için en az 20 karakterlik gerekçe zorunludur."

        if case.risk_class == "CRITICAL" and operator_role != "SOVEREIGN_PRIME" and operator_role != "QUORUM":
            return False, "REQUIRES_OPERATOR_SCOPE: CRITICAL işlemleri sadece PRIME veya QUORUM ezebilir."
            
        if case.requires_quorum and operator_role != "QUORUM":
            return False, "REQUIRES_OPERATOR_SCOPE: Bu işlem QUORUM konsensüsü gerektirir, tekil PRIME ezemez."
            
        return True, "OK"
        
    def can_restore(self, case: GovernorCaseRecord, operator_role: str, archived_at_dt) -> Tuple[bool, str]:
        from datetime import datetime, timezone
        
        if not operator_role:
            return False, "MISSING_OPERATOR_IDENTITY"
            
        if not archived_at_dt:
            return False, "INVALID_STATE: Arşivlenme tarihi bulunamadı."
            
        diff = (datetime.now(timezone.utc) - archived_at_dt).total_seconds()
        if diff > 86400:
            return False, "RESTORE_WINDOW_EXPIRED: 24 saatlik geri alma (restore) penceresi kapandı."
            
        if case.has_safety_lock and operator_role != "SOVEREIGN_PRIME":
            return False, "REQUIRES_OPERATOR_SCOPE: Güvenlik kilitli işlemleri sadece PRIME geri alabilir."
            
        return True, "OK"

execution_policy = ApprovalGovernorExecutionPolicy()
