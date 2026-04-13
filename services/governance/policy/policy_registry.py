"""
Policy Registry — Faz 11

Kural motoru kurallarını koddan dışarı alır.
JSON / dict üzerinden yönetilebilir, API ile güncellenebilir.

Örnek kurallar:
  - auth modülüne otomatik patch yasak
  - diff 150 satırı geçerse manual review
  - migration dosyası varsa auto PR yok
  - reproducer zorunlu (yapılandırılabilir)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from services.observability.logging import get_logger

_log = get_logger("services.governance.policy.policy_registry")


@dataclass
class PolicyRule:
    """Tek bir politika kuralı."""
    name:        str
    description: str
    enabled:     bool   = True
    value:       Any    = None      # Eşik değeri, liste, vb.
    updated_at:  datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by:  str    = "system"

    def to_dict(self) -> dict:
        return {
            "name":        self.name,
            "description": self.description,
            "enabled":     self.enabled,
            "value":       self.value,
            "updated_at":  self.updated_at.isoformat(),
            "updated_by":  self.updated_by,
        }


# ── Varsayılan Kural Seti ─────────────────────────────────────

_DEFAULT_POLICIES: list[PolicyRule] = [
    PolicyRule(
        name="block_auth_module",
        description="auth/ modülüne otomatik patch yasak — her zaman manuel inceleme",
        enabled=True,
        value=["auth/", "auth\\"],
    ),
    PolicyRule(
        name="max_diff_lines_for_auto_pr",
        description="Bu satır sayısını aşan patch'ler otomatik PR alamaz",
        enabled=True,
        value=150,
    ),
    PolicyRule(
        name="block_migration_auto_patch",
        description="alembic/versions/ değişikliği içeren patch otomatik PR alamaz",
        enabled=True,
        value=["alembic/", "alembic\\"],
    ),
    PolicyRule(
        name="require_reproducer_for_create_pr",
        description="create_pr tavsiyesi için reproducer zorunlu mu?",
        enabled=False,     # Zorunlu değil — yapılandırılabilir
        value=True,
    ),
    PolicyRule(
        name="min_confidence_for_auto_pr",
        description="Otomatik PR için minimum güven skoru (%)",
        enabled=True,
        value=60,
    ),
    PolicyRule(
        name="canary_required_before_pr",
        description="PR öncesi canary validation zorunlu mu?",
        enabled=False,     # Varsayılan: opsiyonel
        value=True,
    ),
    PolicyRule(
        name="max_files_for_auto_patch",
        description="Otomatik patch için maksimum dosya sayısı",
        enabled=True,
        value=3,
    ),
    PolicyRule(
        name="block_high_risk_modules",
        description="Yüksek riskli modüllerde auto-PR yok",
        enabled=True,
        value=["main.py", "db/models.py", "db/session.py", "core/orchestrator.py", "config.py"],
    ),
    PolicyRule(
        name="repeat_incident_escalation",
        description="Aynı modülden N adet tekrarlı incident -> manual escalation",
        enabled=True,
        value=3,
    ),
    PolicyRule(
        name="feedback_learning_enabled",
        description="Reject feedback'i root cause ranker'a öğret",
        enabled=True,
        value=True,
    ),
]


class PolicyRegistry:
    """
    Politika kurallarını saklar ve sorgular.
    Runtime'da güncellenebilir.
    """

    def __init__(self):
        self._rules: dict[str, PolicyRule] = {
            r.name: r for r in _DEFAULT_POLICIES
        }

    # ── Okuma ────────────────────────────────────────────────

    def get(self, name: str) -> Optional[PolicyRule]:
        return self._rules.get(name)

    def get_value(self, name: str, default: Any = None) -> Any:
        rule = self._rules.get(name)
        if rule is None or not rule.enabled:
            return default
        return rule.value

    def is_enabled(self, name: str) -> bool:
        rule = self._rules.get(name)
        return rule.enabled if rule else False

    def list_all(self) -> list[dict]:
        return [r.to_dict() for r in self._rules.values()]

    # ── Güncelleme ───────────────────────────────────────────

    def update(self, name: str, enabled: Optional[bool] = None,
               value: Any = None, updated_by: str = "api") -> Optional[PolicyRule]:
        rule = self._rules.get(name)
        if rule is None:
            return None
        if enabled is not None:
            rule.enabled    = enabled
        if value is not None:
            rule.value      = value
        rule.updated_at     = datetime.now(timezone.utc)
        rule.updated_by     = updated_by
        _log.info(f"Policy güncellendi: {name} enabled={rule.enabled} value={rule.value}")
        return rule

    def add(self, rule: PolicyRule) -> PolicyRule:
        self._rules[rule.name] = rule
        _log.info(f"Yeni policy eklendi: {rule.name}")
        return rule

    # ── Yaygın politika kontrolleri (helper) ─────────────────

    def is_module_blocked(self, module_path: str) -> bool:
        blocked = self.get_value("block_auth_module", [])
        return any(module_path.replace("\\", "/").startswith(b.replace("\\", "/"))
                   for b in blocked)

    def is_high_risk_file(self, filepath: str) -> bool:
        hr = self.get_value("block_high_risk_modules", [])
        return filepath in hr

    def max_diff_lines(self) -> int:
        return int(self.get_value("max_diff_lines_for_auto_pr", 150))

    def min_confidence(self) -> int:
        return int(self.get_value("min_confidence_for_auto_pr", 60))

    def max_files(self) -> int:
        return int(self.get_value("max_files_for_auto_patch", 3))

    def repeat_escalation_threshold(self) -> int:
        return int(self.get_value("repeat_incident_escalation", 3))

    def canary_required(self) -> bool:
        return bool(self.get_value("canary_required_before_pr", False))

    # ── JSON import/export ───────────────────────────────────

    def export_json(self) -> str:
        return json.dumps([r.to_dict() for r in self._rules.values()], indent=2, ensure_ascii=False)

    def import_json(self, json_str: str, updated_by: str = "import") -> int:
        data = json.loads(json_str)
        count = 0
        for item in data:
            name = item.get("name")
            if name:
                self.update(name, item.get("enabled"), item.get("value"), updated_by)
                count += 1
        return count


# Singleton
_policy_registry = PolicyRegistry()


def get_policy_registry() -> PolicyRegistry:
    return _policy_registry
