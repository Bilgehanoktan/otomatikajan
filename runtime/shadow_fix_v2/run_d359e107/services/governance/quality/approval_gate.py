"""
İnsan Onayı Kapısı — Faz 3
Yüksek riskli işlemler insan onayı olmadan yürütülmez.

Risk seviyeleri:
  LOW    -> otomatik geç
  MEDIUM -> log ve geç (bildirim gönder)
  HIGH   -> onay bekle (timeout: 30dk)
  CRITICAL -> kesinlikle blokla, onay gerekli

Onay kanalları: in-memory (dev) | webhook bildirimi (prod)
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Awaitable


class ApprovalStatus(str, Enum):
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT  = "timeout"
    AUTO     = "auto"      # Otomatik geçti (düşük risk)


class RiskLevel(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalRequest:
    id:           str
    operation:    str          # "deploy", "schema_change", "external_call" vb.
    description:  str
    risk_level:   RiskLevel
    payload:      dict
    requested_by: str          # agent_id veya user_id
    status:       ApprovalStatus = ApprovalStatus.PENDING
    created_at:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decided_at:   str = ""
    decided_by:   str = ""
    rejection_reason: str = ""
    timeout_s:    float = 1800  # 30 dk varsayılan


# ── İşlem -> Risk Eşleme ───────────────────────────────────
OPERATION_RISK_MAP: dict[str, RiskLevel] = {
    # Kritik
    "production_deploy":        RiskLevel.CRITICAL,
    "database_schema_drop":     RiskLevel.CRITICAL,
    "secret_rotation":          RiskLevel.CRITICAL,
    "bulk_delete":              RiskLevel.CRITICAL,

    # Yüksek
    "architecture_change":      RiskLevel.HIGH,
    "external_webhook_call":    RiskLevel.HIGH,
    "database_migration":       RiskLevel.HIGH,
    "config_update":            RiskLevel.HIGH,
    "destructive_action":       RiskLevel.HIGH,

    # Orta
    "dependency_update":        RiskLevel.MEDIUM,
    "new_integration":          RiskLevel.MEDIUM,
    "permission_change":        RiskLevel.MEDIUM,

    # Düşük
    "code_review":              RiskLevel.LOW,
    "documentation_update":     RiskLevel.LOW,
    "test_run":                 RiskLevel.LOW,
}

# Risk eşiğine göre otomatik geçiş kuralı
AUTO_APPROVE_LEVELS = {RiskLevel.LOW, RiskLevel.MEDIUM}
BLOCK_LEVELS        = {RiskLevel.HIGH, RiskLevel.CRITICAL}


class ApprovalGate:
    """
    Onay kapısı — dev'de in-memory, prod'da webhook entegrasyonlu.
    """

    def __init__(self):
        self._pending:  dict[str, ApprovalRequest]     = {}
        self._history:  list[ApprovalRequest]          = []
        self._notifiers: list[Callable[[ApprovalRequest], Awaitable[None]]] = []

    def add_notifier(self, fn: Callable[[ApprovalRequest], Awaitable[None]]):
        """Onay bildirimi göndermek için callback ekle (webhook, Slack vb.)."""
        self._notifiers.append(fn)

    async def request(
        self,
        operation:   str,
        description: str,
        payload:     dict,
        requested_by:str = "system",
        risk_override: RiskLevel | None = None,
        timeout_s:   float = 1800,
    ) -> ApprovalRequest:
        """
        Bir işlem için onay talep eder.
        - Düşük/orta risk: anında onaylar
        - Yüksek/kritik: bekler ya da bloklar
        """
        risk_level = risk_override or OPERATION_RISK_MAP.get(operation, RiskLevel.MEDIUM)

        req = ApprovalRequest(
            id=str(uuid.uuid4())[:10],
            operation=operation,
            description=description,
            risk_level=risk_level,
            payload=payload,
            requested_by=requested_by,
            timeout_s=timeout_s,
        )

        if risk_level in AUTO_APPROVE_LEVELS:
            req.status     = ApprovalStatus.AUTO
            req.decided_at = datetime.now(timezone.utc).isoformat()
            req.decided_by = "system"
            self._history.append(req)
            return req

        # Yüksek/kritik: kuyruğa al ve bildir
        self._pending[req.id] = req
        await self._notify(req)

        # Timeout ile bekle
        try:
            req = await asyncio.wait_for(
                self._wait_for_decision(req.id),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            req.status     = ApprovalStatus.TIMEOUT
            req.decided_at = datetime.now(timezone.utc).isoformat()
            req.decided_by = "system_timeout"
            self._pending.pop(req.id, None)
            self._history.append(req)

        return req

    async def _wait_for_decision(self, req_id: str) -> "ApprovalRequest":
        while True:
            # Hem pending'de hem history'de ara
            req = self._pending.get(req_id)
            if req is None:
                # Decide edilip history'e taşındı
                for r in reversed(self._history):
                    if r.id == req_id:
                        return r
                # Bulunamadı — timeout
                return ApprovalRequest(
                    id=req_id, operation="unknown", description="",
                    risk_level=RiskLevel.HIGH, payload={}, requested_by="",
                    status=ApprovalStatus.TIMEOUT,
                )
            if req.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
                return req
            await asyncio.sleep(0.05)

    def decide(
        self,
        request_id:  str,
        approve:     bool,
        decided_by:  str = "admin",
        reason:      str = "",
    ) -> ApprovalRequest | None:
        """Manuel onay/red ver (API endpoint'inden çağrılır)."""
        req = self._pending.get(request_id)
        if not req:
            return None

        req.status       = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
        req.decided_at   = datetime.now(timezone.utc).isoformat()
        req.decided_by   = decided_by
        req.rejection_reason = reason if not approve else ""

        self._pending.pop(request_id, None)
        self._history.append(req)
        return req

    async def _notify(self, req: ApprovalRequest):
        for notifier in self._notifiers:
            try:
                await notifier(req)
            except Exception:
                pass

    # ── Sorgulama ─────────────────────────────────────────
    def pending_requests(self) -> list[ApprovalRequest]:
        return list(self._pending.values())

    def history(self, n: int = 50) -> list[ApprovalRequest]:
        return self._history[-n:]

    def stats(self) -> dict:
        hist = self._history
        return {
            "pending":  len(self._pending),
            "total":    len(hist),
            "approved": sum(1 for r in hist if r.status == ApprovalStatus.APPROVED),
            "rejected": sum(1 for r in hist if r.status == ApprovalStatus.REJECTED),
            "auto":     sum(1 for r in hist if r.status == ApprovalStatus.AUTO),
            "timeout":  sum(1 for r in hist if r.status == ApprovalStatus.TIMEOUT),
        }

    def is_blocked(self, req: ApprovalRequest) -> bool:
        """İşlem yürütülmeli mi?"""
        return req.status in (ApprovalStatus.REJECTED, ApprovalStatus.TIMEOUT)

    def is_allowed(self, req: ApprovalRequest) -> bool:
        return req.status in (ApprovalStatus.APPROVED, ApprovalStatus.AUTO)

    def evaluate_policy(self, task_context: dict) -> RiskLevel | None:
        """
        Faz 12.1: Görevin meta verilerine göre otomatik risk seviyesi hesaplar.
        """
        profile = task_context.get("quality_profile", "standard")
        workflow = task_context.get("workflow_template", "default")
        
        # Production profili her zaman yüksek risklidir
        if profile == "production":
            return RiskLevel.HIGH
            
        # Hotfix'ler kritik risklidir
        if workflow == "hotfix":
            return RiskLevel.CRITICAL
            
        # Strict profilli refactor'lar yüksek risklidir
        if workflow == "refactor" and profile == "strict":
            return RiskLevel.HIGH
            
        return None

# Singleton
approval_gate = ApprovalGate()
