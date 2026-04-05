"""
WorldModel Katman 9.2: Service Dependency Graph
[FIX-9] Servis sağlığı ve bağımlılıklarını gerçek zamanlı takip eder.
SystemController, ModelOrchestrator, DB ve diğer kritik servislerin
operasyonel durumunu modelleyerek AGI'nin karar vermesine bağlam sağlar.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from packages.observability.logging import get_logger

_log = get_logger("world_service_graph")


@dataclass
class ServiceNode:
    """Bir servis biriminin anlık durumu."""
    service_id: str
    name: str
    status: str = "unknown"          # healthy | degraded | down | unknown
    health_score: float = 1.0        # 0.0 – 1.0
    dependencies: List[str] = field(default_factory=list)  # diğer service_id'ler
    last_checked: Optional[datetime] = None
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_healthy(self):
        self.status = "healthy"
        self.health_score = min(1.0, self.health_score + 0.1)
        self.failure_count = 0
        self.last_checked = datetime.now(timezone.utc)

    def mark_degraded(self, reason: str = ""):
        self.status = "degraded"
        self.health_score = max(0.3, self.health_score - 0.2)
        self.failure_count += 1
        self.last_checked = datetime.now(timezone.utc)
        if reason:
            self.metadata["last_degradation_reason"] = reason

    def mark_down(self, reason: str = ""):
        self.status = "down"
        self.health_score = 0.0
        self.failure_count += 1
        self.last_checked = datetime.now(timezone.utc)
        if reason:
            self.metadata["last_down_reason"] = reason


class ServiceDependencyGraph:
    """
    WorldModel Katman 9.2: Servis bağımlılık grafiği.
    AGI, plan yaparken hangi servislerin sağlıklı, hangilerinin çökmüş olduğunu bilir.
    """

    def __init__(self):
        self._nodes: Dict[str, ServiceNode] = {}
        self._register_core_services()

    def _register_core_services(self):
        """Sistem içindeki temel servisleri kayıt eder."""
        core = [
            ServiceNode("llm_orchestrator", "LLM Orchestrator",
                        dependencies=["api_gateway"]),
            ServiceNode("api_gateway", "API Gateway"),
            ServiceNode("postgresql", "PostgreSQL",
                        dependencies=[]),
            ServiceNode("redis", "Redis Cache",
                        dependencies=[]),
            ServiceNode("synaptic_cortex", "Synaptic Cortex (Memory)",
                        dependencies=["postgresql"]),
            ServiceNode("job_queue", "Job Queue",
                        dependencies=["postgresql"]),
            ServiceNode("telegram_bot", "Telegram Bot",
                        dependencies=["api_gateway"]),
            ServiceNode("ws_manager", "WebSocket Manager",
                        dependencies=["api_gateway"]),
            ServiceNode("affective_core", "Affective Core",
                        dependencies=["synaptic_cortex"]),
            ServiceNode("policy_engine", "Policy Evolution Engine",
                        dependencies=["llm_orchestrator", "synaptic_cortex"]),
        ]
        for svc in core:
            self._nodes[svc.service_id] = svc
        _log.info(f"[SERVICE-GRAPH] {len(self._nodes)} çekirdek servis kayıt edildi.")

    def update_status(self, service_id: str, status: str, health_score: float = None, reason: str = ""):
        """Bir servisin durumunu günceller."""
        if service_id not in self._nodes:
            self._nodes[service_id] = ServiceNode(service_id, service_id)

        node = self._nodes[service_id]
        if status == "healthy":
            node.mark_healthy()
        elif status == "degraded":
            node.mark_degraded(reason)
        elif status == "down":
            node.mark_down(reason)
        else:
            node.status = status
            node.last_checked = datetime.now(timezone.utc)

        if health_score is not None:
            node.health_score = max(0.0, min(1.0, health_score))

    def get_critical_path_status(self) -> Dict[str, Any]:
        """
        AGI'nin kritik çalışma yolundaki servis sağlığını döner.
        Karar verme sürecine bağlam sağlar.
        """
        total = len(self._nodes)
        healthy = sum(1 for n in self._nodes.values() if n.status == "healthy")
        degraded = sum(1 for n in self._nodes.values() if n.status == "degraded")
        down = [n.service_id for n in self._nodes.values() if n.status == "down"]
        avg_health = sum(n.health_score for n in self._nodes.values()) / total if total else 0.0

        return {
            "total_services": total,
            "healthy": healthy,
            "degraded": degraded,
            "down_services": down,
            "average_health_score": round(avg_health, 3),
            "system_operational": len(down) == 0,
        }

    def get_impacted_services(self, failed_service_id: str) -> List[str]:
        """Bir servis düştüğünde etkilenen (bağımlı) servisleri bulur."""
        impacted = []
        for node in self._nodes.values():
            if failed_service_id in node.dependencies:
                impacted.append(node.service_id)
        return impacted

    def get_summary(self) -> Dict[str, Any]:
        """AGI'ye aktarılacak özet (ContextPackage entegrasyonu için)."""
        status = self.get_critical_path_status()
        status["nodes"] = {
            sid: {"status": n.status, "health": n.health_score, "failures": n.failure_count}
            for sid, n in self._nodes.items()
        }
        return status

    async def pulse_check(self, model_orch=None) -> Dict[str, Any]:
        """
        Mevcut sistem bileşenlerinden gerçek zamanlı sağlık verisi çeker.
        ModelOrchestrator, DB ve temel servisleri gerçekten sorgular.
        """
        # LLM Orchestrator
        try:
            if model_orch:
                score = model_orch.get_health_score()
                self.update_status("llm_orchestrator", "healthy" if score > 0.5 else "degraded",
                                   health_score=score)
        except Exception:
            self.update_status("llm_orchestrator", "down", reason="Health check failed")

        # PostgreSQL
        try:
            from packages.persistence.session import is_db_available
            db_ok = await is_db_available()
            self.update_status("postgresql", "healthy" if db_ok else "down",
                               health_score=1.0 if db_ok else 0.0)
        except Exception:
            self.update_status("postgresql", "down", reason="DB connection failed")

        return self.get_summary()


# Singleton
service_graph = ServiceDependencyGraph()
