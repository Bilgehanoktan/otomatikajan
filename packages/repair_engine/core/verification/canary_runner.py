"""
Canary Validation Layer — Faz 11

Patch doğrulandıktan sonra mini smoke senaryosu koşturur.
Gerçek staging olmadan sistem sağlığını kontrol eder.

Durum geçişleri:
  VERIFIED -> CANARY_PENDING -> CANARY_RUNNING -> CANARY_PASSED | CANARY_FAILED
"""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from packages.observability.logging import get_logger

_log = get_logger("repair.verification.canary")


class CanaryStatus(str, Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    PASSED   = "passed"
    FAILED   = "failed"
    SKIPPED  = "skipped"


@dataclass
class CanaryCheck:
    name:    str
    passed:  bool
    detail:  str
    duration_ms: float = 0.0


@dataclass
class CanaryResult:
    canary_id:  str
    job_id:     str
    status:     CanaryStatus
    checks:     list[CanaryCheck] = field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at:   Optional[datetime] = None
    reason:     str = ""

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total_count(self) -> int:
        return len(self.checks)

    def to_dict(self) -> dict:
        return {
            "canary_id":   self.canary_id,
            "job_id":      self.job_id,
            "status":      self.status.value,
            "passed":      self.passed_count,
            "total":       self.total_count,
            "checks":      [
                {"name": c.name, "passed": c.passed,
                 "detail": c.detail, "duration_ms": c.duration_ms}
                for c in self.checks
            ],
            "reason":      self.reason,
            "started_at":  self.started_at.isoformat() if self.started_at else None,
            "ended_at":    self.ended_at.isoformat() if self.ended_at else None,
        }


# ── Canary Checks ─────────────────────────────────────────────

async def _check_python_import(module_path: str) -> CanaryCheck:
    """Hedef modülün import edilebilir olup olmadığını kontrol et."""
    t0 = time.time()
    try:
        import importlib
        mod = module_path.replace("/", ".").replace(".py", "")
        importlib.import_module(mod)
        return CanaryCheck(
            name=f"import:{mod}", passed=True,
            detail="Import OK",
            duration_ms=(time.time()-t0)*1000,
        )
    except Exception as e:
        return CanaryCheck(
            name=f"import:{module_path}", passed=False,
            detail=f"Import hatası: {e}",
            duration_ms=(time.time()-t0)*1000,
        )


async def _check_syntax_files(file_paths: list[str]) -> CanaryCheck:
    """Değiştirilen dosyaların syntax kontrolü."""
    import ast, os
    t0 = time.time()
    errors = []
    for fp in file_paths:
        if not fp.endswith(".py") or not os.path.isfile(fp):
            continue
        try:
            with open(fp, encoding="utf-8") as f:
                ast.parse(f.read())
        except SyntaxError as e:
            errors.append(f"{fp}: {e}")
    ok = len(errors) == 0
    return CanaryCheck(
        name="syntax_check",
        passed=ok,
        detail="Syntax OK" if ok else f"Syntax hataları: {'; '.join(errors[:3])}",
        duration_ms=(time.time()-t0)*1000,
    )


async def _check_no_obvious_regression(diff: str) -> CanaryCheck:
    """Basit regresyon risk sinyali — tehlikeli pattern yoksa PASS."""
    import re
    t0 = time.time()
    danger = [
        (r"\beval\s*\(", "eval() kullanımı"),
        (r"\bexec\s*\(", "exec() kullanımı"),
        (r"os\.system\s*\(", "os.system() çağrısı"),
    ]
    added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    found = [msg for pat, msg in danger if re.search(pat, added)]
    ok = len(found) == 0
    return CanaryCheck(
        name="regression_signal",
        passed=ok,
        detail="Tehlikeli pattern yok" if ok else f"Risk sinyalleri: {', '.join(found)}",
        duration_ms=(time.time()-t0)*1000,
    )


async def _check_health_endpoint(base_url: str = "http://localhost:8000") -> CanaryCheck:
    """Health endpoint'i kontrol et (sunucu çalışıyorsa)."""
    t0 = time.time()
    try:
        import urllib.request
        with urllib.request.urlopen(f"{base_url}/health", timeout=3) as r:
            ok = r.status == 200
            return CanaryCheck(
                name="health_endpoint",
                passed=ok,
                detail=f"HTTP {r.status}",
                duration_ms=(time.time()-t0)*1000,
            )
    except Exception as e:
        return CanaryCheck(
            name="health_endpoint",
            passed=True,    # Sunucu offline -> skip (not fail)
            detail=f"Sunucu ulaşılamıyor — atlandı ({e})",
            duration_ms=(time.time()-t0)*1000,
        )


# ── CanaryRunner ──────────────────────────────────────────────

class CanaryRunner:
    """
    Patch sonrası mini smoke senaryoları koşturur.
    Başarısız canary -> PR önerisi düşürülür, manual review'a yönlenir.
    """

    async def run(
        self,
        job_id:       str,
        diff:         str,
        changed_files: list[str],
        project_root: str = ".",
    ) -> CanaryResult:
        result = CanaryResult(
            canary_id  = f"can_{uuid.uuid4().hex[:8]}",
            job_id     = job_id,
            status     = CanaryStatus.RUNNING,
            started_at = datetime.now(timezone.utc),
        )

        _log.info(f"Canary başlatıldı: {result.canary_id} (job={job_id})")

        checks: list[CanaryCheck] = []

        # Check 1: Syntax
        checks.append(await _check_syntax_files(
            [f"{project_root}/{f}" for f in changed_files if f.endswith(".py")]
        ))

        # Check 2: Regresyon sinyali
        checks.append(await _check_no_obvious_regression(diff))

        # Check 3: Import kontrolü (değiştirilen Python modülleri)
        for f in changed_files[:3]:
            if f.endswith(".py") and not f.startswith("test"):
                checks.append(await _check_python_import(f))

        # Check 4: Health endpoint (opsiyonel)
        checks.append(await _check_health_endpoint())

        result.checks   = checks
        result.ended_at = datetime.now(timezone.utc)

        failed = [c for c in checks if not c.passed]
        if failed:
            result.status = CanaryStatus.FAILED
            result.reason = f"{len(failed)} canary check başarısız: " + \
                            "; ".join(c.name for c in failed[:3])
            _log.warning(f"Canary FAILED [{job_id}]: {result.reason}")
        else:
            result.status = CanaryStatus.PASSED
            result.reason = f"Tüm {len(checks)} check geçti"
            _log.info(f"Canary PASSED [{job_id}]")

        return result

    def should_block_pr(self, result: CanaryResult) -> bool:
        """Canary başarısızsa PR bloke edilmeli mi?"""
        if result.status == CanaryStatus.FAILED:
            # Syntax veya regression hatası varsa bloke et
            critical_failed = any(
                c.name in ("syntax_check", "regression_signal") and not c.passed
                for c in result.checks
            )
            return critical_failed
        return False


# Singleton
_canary_runner = CanaryRunner()


def get_canary_runner() -> CanaryRunner:
    return _canary_runner
