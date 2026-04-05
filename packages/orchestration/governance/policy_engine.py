import json
import os
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List, Dict, Any

from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
from packages.repair_engine.schemas.patch_plan import PatchPlan, RiskLevel
from packages.repair_engine.schemas.validation import ValidationReport
from packages.observability.logging import get_logger

_log = get_logger("core.policy_engine")

class AutomationLevel(int, Enum):
    REPORT_ONLY = 0    # Sadece rapor
    CREATE_PR   = 1    # Branch + PR (maksimum izin)
    AUTO_MERGE  = 2    # Otomatik merge (KAPALI)
    AUTO_DEPLOY = 3    # Production deploy (KAPALI)

@dataclass
class PolicyDecision:
    allowed:              bool
    automation_level:     AutomationLevel
    requires_human:       bool
    blocking_reasons:     list[str]
    warnings:             list[str]
    recommended_action:   str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["automation_level"] = self.automation_level.name
        return d

class PolicyEngine:
    """
    Repair Pipeline Policy Engine (core.policy_engine).
    Hangi kararın nerede otomasyon alabileceğini yöneten dinamik motor.
    NOT: AGI adaptif politika motoru ile karıştırılmamalıdır.
    AGI adaptif motor: core.agi.adaptation.policy_engine.PolicyEngine
    """
    POLICY_FILE = "config/policies.json"

    def __init__(self):
        self._load_policies()
        self._decisions: list[dict] = []

    def _load_policies(self):
        try:
            if os.path.exists(self.POLICY_FILE):
                with open(self.POLICY_FILE, "r") as f:
                    data = json.load(f)
            else:
                data = {
                    "max_automation": 1,
                    "blocked_modules": ["auth", "jwt_auth"],
                    "blocked_file_prefixes": ["auth/", "alembic/"],
                    "high_risk_files": ["main.py", "config.py"],
                    "automation_thresholds": {"confidence_min": 60, "max_files": 3}
                }
            
            self.max_automation = AutomationLevel(data.get("max_automation", 1))
            self.blocked_modules = set(data.get("blocked_modules", []))
            self.blocked_prefixes = data.get("blocked_file_prefixes", [])
            self.high_risk_files = set(data.get("high_risk_files", []))
            self.thresholds = data.get("automation_thresholds", {})
            self.learned_policies = data.get("learned_policies", [])
            _log.info("Policies loaded successfully.")
        except Exception as e:
            _log.error(f"Policy loading error: {e}")
            # Fallback to defaults
            self.max_automation = AutomationLevel.CREATE_PR
            self.blocked_modules = {"auth"}
            self.blocked_prefixes = ["auth/"]
            self.high_risk_files = {"main.py"}
            self.thresholds = {"confidence_min": 60, "max_files": 3}

    def save(self):
        """Mevcut politikaları kalıcı depolamaya yazar."""
        try:
            data = {
                "max_automation": int(self.max_automation),
                "blocked_modules": list(self.blocked_modules),
                "blocked_file_prefixes": self.blocked_prefixes,
                "high_risk_files": list(self.high_risk_files),
                "automation_thresholds": self.thresholds,
                "learned_policies": self.learned_policies
            }
            with open(self.POLICY_FILE, "w") as f:
                json.dump(data, f, indent=2)
            _log.info("Policies saved to disk.")
        except Exception as e:
            _log.error(f"Policy save error: {e}")

    def evolve_policy(self, update_data: Dict[str, Any]):
        """
        Dışarıdan (PolicyEvolutionEngine vb.) gelen verilerle politikayı günceller.
        """
        if "max_automation" in update_data:
            new_level = AutomationLevel(update_data["max_automation"])
            if new_level <= AutomationLevel.AUTO_MERGE: # Hard limit for now
                self.max_automation = new_level
        
        if "add_high_risk" in update_data:
            self.high_risk_files.add(update_data["add_high_risk"])
        
        if "remove_high_risk" in update_data and update_data["remove_high_risk"] in self.high_risk_files:
            self.high_risk_files.remove(update_data["remove_high_risk"])

        if "thresholds" in update_data:
            self.thresholds.update(update_data["thresholds"])
        
        self.save()

    def evaluate_patch(
        self,
        ticket:     DiagnosisTicket,
        plan:       PatchPlan,
        validation: ValidationReport,
        job_id:     str = "unknown",
    ) -> PolicyDecision:
        blocking:  list[str] = []
        warnings:  list[str] = []

        # 1. Engellenen modüller
        for f in plan.target_files:
            module = f.split("/")[0]
            if module in self.blocked_modules or any(f.startswith(p) for p in self.blocked_prefixes):
                blocking.append(f"Engellenen modül: {f}")

        # 2. Yüksek riskli dosyalar
        for f in plan.target_files:
            if f in self.high_risk_files:
                warnings.append(f"Yüksek riskli dosya: {f}")

        # 3. Validation durumu
        if not validation.syntax_ok:
            blocking.append("Syntax kontrolü başarısız")
        if not validation.security_ok:
            blocking.append("Güvenlik taraması başarısız")

        # 4. Risk ve Thresholdlar
        conf_min = self.thresholds.get("confidence_min", 60)
        if validation.confidence < conf_min:
            blocking.append(f"Confidence yetersiz: {validation.confidence} < {conf_min}")

        if len(plan.target_files) > self.thresholds.get("max_files", 3):
            warnings.append(f"Çok fazla dosya değişikliği ({len(plan.target_files)})")

        # Karar
        if blocking:
            level   = AutomationLevel.REPORT_ONLY
            action  = "manual_review_only" if validation.syntax_ok else "reject"
            allowed = False
        else:
            level   = self.max_automation
            action  = "create_pr" if level >= AutomationLevel.CREATE_PR else "report_only"
            allowed = True

        decision = PolicyDecision(
            allowed=allowed,
            automation_level=level,
            requires_human=not allowed or level < AutomationLevel.AUTO_MERGE,
            blocking_reasons=blocking,
            warnings=warnings,
            recommended_action=action,
        )

        self._decisions.append({
            "job_id": job_id,
            "action": action,
            "allowed": allowed
        })
        return decision

    def evaluate_triage(self, ticket: DiagnosisTicket) -> PolicyDecision:
        blocking = []
        if ticket.classification in (ProblemClass.SECURITY_VIOLATION, ProblemClass.AUTH_FAILURE):
            blocking.append("Güvenlik ihlali tespiti")
        
        allowed = len(blocking) == 0
        return PolicyDecision(
            allowed=allowed,
            automation_level=AutomationLevel.REPORT_ONLY if not allowed else self.max_automation,
            requires_human=not allowed,
            blocking_reasons=blocking,
            warnings=[],
            recommended_action="continue" if allowed else "manual_review_only"
        )

    def stats(self) -> dict:
        total = len(self._decisions)
        success_rate = sum(1 for d in self._decisions if d["allowed"]) / total if total > 0 else 1.0
        return {
            "total_evaluated": total,
            "success_rate": round(success_rate, 2),
            "current_max_automation": self.max_automation.name
        }

# Singleton
policy_engine = PolicyEngine()

# Alias for disambiguation
RepairPolicyEngine = PolicyEngine
repair_policy_engine = policy_engine
