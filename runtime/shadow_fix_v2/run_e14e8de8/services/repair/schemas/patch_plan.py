"""
PatchPlan — Patch üretiminden önce üretilen minimal değişiklik planı.
Kod yazmadan önce hedef, risk ve test net olmalı.

Faz 10.1: reproducer_tests, verification_mode, allowed_commands,
           requires_manual_review_reason alanları eklendi.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ChangeType(str, Enum):
    ADD_IMPORT        = "add_import"
    FIX_SYMBOL        = "fix_symbol"
    FIX_RETURN_TYPE   = "fix_return_type"
    ADD_NULL_CHECK    = "add_null_check"
    FIX_CONTRACT      = "fix_contract"
    ADD_ERROR_HANDLER = "add_error_handler"
    FIX_STATE_MAP     = "fix_state_map"
    CONFIG_REPAIR     = "config_repair"
    DEPENDENCY_FIX    = "dependency_fix"
    TEST_ADD          = "test_add"
    UNKNOWN           = "unknown"


class RiskLevel(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


@dataclass
class PatchAction:
    file:          str
    symbol:        Optional[str]    # hangi fonksiyon/sınıf
    change_type:   ChangeType
    description:   str
    line_hint:     Optional[int]    = None
    backward_safe: bool             = True

    def to_dict(self) -> dict:
        return {
            "file":          self.file,
            "symbol":        self.symbol,
            "change_type":   self.change_type.value,
            "description":   self.description,
            "line_hint":     self.line_hint,
            "backward_safe": self.backward_safe,
        }


# Varsayılan sandbox komut izin listesi
DEFAULT_ALLOWED_COMMANDS = [
    "python3 -m pytest",
    "python3 -m compileall",
    "python3 -c",
    "ruff",
    "mypy",
    "git diff",
    "git checkout -b",
]


@dataclass
class PatchPlan:
    """Patch üretilmeden önce onaylanan plan."""

    plan_id:               str
    ticket_id:             str
    target_files:          list[str]          = field(default_factory=list)
    actions:               list[PatchAction]  = field(default_factory=list)
    risk:                  RiskLevel          = RiskLevel.LOW
    public_api_impact:     bool               = False
    migration_required:    bool               = False
    backward_compatible:   bool               = True
    # Standart test dosyaları
    required_tests:        list[str]          = field(default_factory=list)
    # Bug'ı yeniden üreten özel test — patch öncesi FAIL, sonrası PASS olmalı
    reproducer_tests:      list[str]          = field(default_factory=list)
    # strict -> tüm kapılar | lenient -> syntax+security | syntax_only
    verification_mode:     str                = "strict"
    # Sandbox izin listesi; None -> DEFAULT_ALLOWED_COMMANDS kullanılır
    allowed_commands:      Optional[list[str]] = None
    # Manuel inceleme zorunluysa neden
    requires_manual_review_reason: str        = ""
    rollback_strategy:     str                = ""
    rationale:             str                = ""
    approved:              bool               = False
    created_at:            datetime           = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def create(cls, ticket_id: str, **kwargs) -> "PatchPlan":
        return cls(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            ticket_id=ticket_id,
            **kwargs,
        )

    def is_safe_for_auto_patch(self) -> bool:
        """Bu plan otomatik patch için güvenli mi?"""
        return (
            self.risk == RiskLevel.LOW
            and not self.public_api_impact
            and not self.migration_required
            and self.backward_compatible
            and len(self.target_files) <= 3
        )

    def effective_allowed_commands(self) -> list[str]:
        """Sandbox'ta izin verilen komutları döndür."""
        return self.allowed_commands if self.allowed_commands is not None else DEFAULT_ALLOWED_COMMANDS

    def to_dict(self) -> dict:
        return {
            "plan_id":                       self.plan_id,
            "ticket_id":                     self.ticket_id,
            "target_files":                  self.target_files,
            "actions":                       [a.to_dict() for a in self.actions],
            "risk":                          self.risk.value,
            "public_api_impact":             self.public_api_impact,
            "migration_required":            self.migration_required,
            "backward_compatible":           self.backward_compatible,
            "required_tests":                self.required_tests,
            "reproducer_tests":              self.reproducer_tests,
            "verification_mode":             self.verification_mode,
            "allowed_commands":              self.effective_allowed_commands(),
            "requires_manual_review_reason": self.requires_manual_review_reason,
            "rollback_strategy":             self.rollback_strategy,
            "rationale":                     self.rationale,
            "approved":                      self.approved,
            "safe_for_auto":                 self.is_safe_for_auto_patch(),
            "created_at":                    self.created_at.isoformat(),
        }
