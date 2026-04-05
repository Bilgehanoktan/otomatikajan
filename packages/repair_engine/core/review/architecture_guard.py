"""
Architecture Guard — Faz 11

Patch mimariyi bozmasın diye statik kural kontrolü yapar.
Import graph + forbidden dependency listesi + layering policy.

Kontroller:
  - API router -> repository doğrudan çağırıyor mu?
  - auth modülü UI katmanına sızıyor mu?
  - orchestrator DB model import ediyor mu?
  - Döngüsel bağımlılık var mı?
  - Forbidden import pattern'ları var mı?
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from packages.observability.logging import get_logger

_log = get_logger("repair.review.architecture_guard")


@dataclass
class ArchitectureViolation:
    rule:        str
    file:        str
    detail:      str
    severity:    str   # "error" | "warning"
    line_hint:   Optional[int] = None


@dataclass
class ArchitectureGuardResult:
    passed:     bool
    violations: list[ArchitectureViolation] = field(default_factory=list)
    checked_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed":        self.passed,
            "violation_count": len(self.violations),
            "violations": [
                {"rule": v.rule, "file": v.file, "detail": v.detail,
                 "severity": v.severity, "line_hint": v.line_hint}
                for v in self.violations
            ],
            "checked_files": self.checked_files,
        }


# ── Forbidden Patterns ────────────────────────────────────────

# (source_prefix, forbidden_import_pattern, rule_name, severity)
_FORBIDDEN_IMPORTS = [
    # Global circular import prevention
    ("",        r"from main import",                "circular_import_main", "error"),
    ("",        r"import main",                     "direct_import_main",   "warning"),
    
    # API router -> DB model/session doğrudan alamaz (repository katmanı üzerinden gitmeli)
    ("api/",    r"from db\.models import",          "api_direct_db_model",  "error"),
    ("api/",    r"from db\.session import",         "api_direct_db_session","warning"),
    ("api/",    r"import packages.persistence\.models",               "api_direct_db_model_2","error"),
    
    # Auth modülü UI/API'ya çıkmamalı
    ("auth/",   r"from api\.",                      "auth_to_api",          "error"),
    ("auth/",   r"from dashboard",                  "auth_to_dashboard",    "error"),
    
    # Orchestrator DB model import etmemeli
    ("core/orchestrator", r"from db\.models",       "orchestrator_db_model","warning"),
    
    # Repair modülü production dosyalarına doğrudan yazamaz
    ("repair/", r"open\(.+['\"]w['\"]",             "repair_direct_write",  "error"),
    
    # Test dosyaları ana koda import olarak eklenmemeli
    ("api/",    r"from tests\.",                    "api_imports_tests",    "error"),
    ("core/",   r"from tests\.",                    "core_imports_tests",   "error"),
    
    # Gelişmiş güvenlik: os.system yasak (subprocess kullan)
    ("",        r"os\.system\(",                    "forbidden_os_system",  "error"),
]

# Katman sıralaması: düşük -> yüksek (yüksek katman düşüğü import edemez)
_LAYER_ORDER = [
    "db/",           # en alt — sadece kendisi + stdlib
    "auth/",
    "observability/",
    "memory/",
    "llm/",
    "agents/",
    "core/",
    "repair/",
    "heal/",
    "tasks/",
    "api/",          # en üst
]


def _file_layer(filepath: str) -> Optional[int]:
    fp = filepath.replace("\\", "/")
    for i, prefix in enumerate(_LAYER_ORDER):
        if fp.startswith(prefix):
            return i
    return None


class ArchitectureGuard:
    """
    Diff içindeki yeni satırları mimari kurallara göre denetler.
    """

    def check_diff(self, diff: str, changed_files: Optional[list[str]] = None) -> ArchitectureGuardResult:
        violations: list[ArchitectureViolation] = []
        checked:    list[str] = []
        current_file = ""

        for line in diff.splitlines():
            # Dosya başlığı
            m = re.match(r"^\+\+\+ b/(.+)$", line)
            if m:
                current_file = m.group(1)
                checked.append(current_file)
                continue

            # Sadece yeni eklenen satırlar
            if not line.startswith("+") or line.startswith("+++"):
                continue

            code_line = line[1:]
            line_num  = None  # diff'ten satır no çıkarmak opsiyonel

            # Forbidden import kontrolleri
            for src_prefix, pattern, rule, severity in _FORBIDDEN_IMPORTS:
                if current_file.replace("\\", "/").startswith(src_prefix):
                    if re.search(pattern, code_line):
                        violations.append(ArchitectureViolation(
                            rule=rule,
                            file=current_file,
                            detail=f"Yasak pattern: '{code_line.strip()[:80]}'",
                            severity=severity,
                            line_hint=line_num,
                        ))

            # Katman ihlali
            import_m = re.search(r"from ([\w./]+) import", code_line)
            if import_m:
                imp_path = import_m.group(1).replace(".", "/")
                src_layer = _file_layer(current_file)
                imp_layer = _file_layer(imp_path + "/")
                if src_layer is not None and imp_layer is not None:
                    if imp_layer > src_layer:
                        violations.append(ArchitectureViolation(
                            rule="layer_violation",
                            file=current_file,
                            detail=(
                                f"Üst katman import: {current_file} "
                                f"(layer={src_layer}) -> {imp_path} (layer={imp_layer})"
                            ),
                            severity="warning",
                        ))

        # Sadece error severity olanlar "passed=False" yapar
        errors = [v for v in violations if v.severity == "error"]
        passed = len(errors) == 0

        if violations:
            _log.info(
                f"Architecture guard: {len(violations)} ihlal "
                f"({len(errors)} error, {len(violations)-len(errors)} warning)"
            )

        return ArchitectureGuardResult(
            passed=passed,
            violations=violations,
            checked_files=checked,
        )


_guard = ArchitectureGuard()


def get_architecture_guard() -> ArchitectureGuard:
    return _guard
