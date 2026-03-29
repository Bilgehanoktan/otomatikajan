import asyncio
import hashlib
import logging
import warnings
from typing import List
from datetime import datetime, timedelta
from .models import ImprovementOpportunity
from db.repository import ApiMetricRepository, ProjectRepository

# Faz 12.1 Cleanup: Legacy observer is deprecated
warnings.warn("improve.observer is deprecated. Use core.improvement.observer instead.", DeprecationWarning, stacklevel=2)

logger = logging.getLogger(__name__)

# Faz 10.1: Route ownership map — hardcoded "task_router.py" kaldırıldı
# endpoint prefix -> kaynak dosya ilişkisi
_ENDPOINT_OWNER_MAP = {
    "/tasks":              "api/task_read_router.py",
    "/tasks/*/cancel":     "api/task_control_router.py",
    "/tasks/*/retry":      "api/task_control_router.py",
    "/tasks/*/stop":       "api/task_control_router.py",
    "/auth":               "auth/jwt_auth.py",
    "/repair":             "api/repair_router.py",
    "/improve":            "api/improvement_router.py",
    "/code":               "api/code_router.py",
    "/monitoring":         "api/monitoring_router.py",
    "/":                   "dashboard/index.html",
}


def _endpoint_to_file(endpoint: str) -> str:
    """Endpoint path'ini sahibi dosyaya çevir."""
    for prefix, owner in _ENDPOINT_OWNER_MAP.items():
        clean_prefix = prefix.replace("*", "")
        if endpoint.startswith(clean_prefix.rstrip("/")):
            return owner
    return "api/task_read_router.py"  # fallback

class ImprovementObserver:
    """Detects improvement opportunities by scanning system metrics and logs."""

    def __init__(self, db_session):
        self.db = db_session

    async def scan(self) -> List[ImprovementOpportunity]:
        """
        Scans metrics (API latency, error rates) and health logs.
        """
        opportunities = []
        
        # 1. Scan API Metrics for high error rates (> 5%) or high latency (> 5s)
        try:
            stats = await ApiMetricRepository.endpoint_stats(self.db, hours=1)
            for s in stats:
                endpoint = s["endpoint"]
                
                # SRE Hardening: Kendi endpointlerimizin hatalarını raporlayıp döngüye girmesini engelle
                if "/improvements/apply-proposal" in endpoint or "/improvements/scan" in endpoint:
                    continue

                # Deterministik ID oluştur (endpoint + method + metric_type)
                # Bu sayede her taramada aynı ID oluşur ve 'Uygula' butonu çalışır.
                def generate_id(suffix: str):
                    raw = f"{endpoint}:{s['method']}:{suffix}"
                    return hashlib.sha256(raw.encode()).hexdigest()[:16]

                if s["error_rate"] > 5.0:
                    opportunities.append(ImprovementOpportunity(
                        id=f"api_err_{generate_id('error')}",
                        source_metric="api_error_rate",
                        severity="high",
                        description=f"Endpoint {endpoint} has high error rate: {s['error_rate']}%",
                        affected_files=[_endpoint_to_file(endpoint)],
                        evidence=s
                    ))
                if s["avg_ms"] > 5000:
                    opportunities.append(ImprovementOpportunity(
                        id=f"api_lat_{generate_id('latency')}",
                        source_metric="api_latency",
                        severity="medium",
                        description=f"Endpoint {endpoint} is slow: {s['avg_ms']}ms",
                        affected_files=[_endpoint_to_file(endpoint)],
                        evidence=s
                    ))
        except Exception as e:
            logger.error(f"Observer failed to scan API metrics: {e}")

        # 2. Scan Project failures
        try:
            recent_projects = await ProjectRepository.list_recent(self.db, limit=50, status="error")
            if len(recent_projects) >= 3:
                # Deterministik ID (failure count + status)
                proj_id = hashlib.sha256(f"project_failure:{len(recent_projects)}".encode()).hexdigest()[:16]
                opportunities.append(ImprovementOpportunity(
                    id=f"proj_fail_{proj_id}",
                    source_metric="agent_failure",
                    severity="high",
                    description=f"Multiple recent project failures detected ({len(recent_projects)})",
                    affected_files=["heal/recovery_strategies.py"],
                    evidence={"count": len(recent_projects)}
                ))
        except Exception as e:
            logger.error(f"Observer failed to scan project metrics: {e}")
        
        return opportunities

    async def prioritize(self, opportunities: List[ImprovementOpportunity]) -> List[ImprovementOpportunity]:
        """Sorts opportunities by severity."""
        severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        return sorted(opportunities, key=lambda x: severity_map.get(x.severity, 0), reverse=True)
