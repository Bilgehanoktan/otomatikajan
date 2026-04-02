import uuid
import hashlib
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

from db.session import AsyncSessionLocal
from db.repository import ProjectRepository, ApiMetricRepository
from memory.watchdog import watchdog
from core.agency.loader import agency_loader
from observability.logging import get_logger

logger = get_logger("agi.cognitive.auditor")

class SovereignCortexAuditor:
    """
    Sovereign AGI Birleşik Denetim Merkezi (Auditor).
    Sistemin operasyonel, teknik ve bilişsel açıklarını tespit eder.
    """
    def __init__(self):
        self.threshold_error_rate = 5.0  # %5 hata eşiği
        self.threshold_latency_ms = 5000 # 5 saniye gecikme eşiği
        self.min_occurrences = 3        # Tekrarlanan hata eşiği

    async def run_full_audit(self) -> List[Dict[str, Any]]:
        """Tüm sistem katmanlarını tarar ve bulguları döner."""
        logger.info("[AUDIT] Sovereign Cortex: Sistem genel denetimi başlatılıyor...")
        
        findings = []
        
        # 1. API ve Performans Denetimi
        findings.extend(await self._audit_api_metrics())
        
        # 2. Watchdog ve Anomali Denetimi
        findings.extend(await self._audit_watchdog_events())
        
        # 3. Proje ve Görev Basarisizlik Denetimi
        findings.extend(await self._audit_project_failures())
        
        # 4. Yetenek ve Kapasite Gaping (AGI Gap)
        findings.extend(await self._audit_capacity_gaps())
        
        logger.info(f"[AUDIT] Sovereign Cortex: Denetim tamamlandi. {len(findings)} bulgu tespit edildi.")
        return findings

    async def _audit_api_metrics(self) -> List[Dict[str, Any]]:
        """API hata oranları ve gecikme sürelerini denetler."""
        ops = []
        try:
            async with AsyncSessionLocal() as db:
                stats = await ApiMetricRepository.endpoint_stats(db, hours=1)
                for s in stats:
                    endpoint = s["endpoint"]
                    
                    # Döngüsel raporlamayı engelle
                    if "/improvements/" in endpoint or "/audit/" in endpoint:
                        continue

                    # Hata Oranı Denetimi
                    if s["error_rate"] > self.threshold_error_rate:
                        ops.append({
                            "id": f"api_err_{self._generate_hash(endpoint + 'error')}",
                            "category": "performance",
                            "source_type": "api_error_rate",
                            "severity": "high",
                            "title": f"Yüksek Hata Oranı: {endpoint}",
                            "description": f"'{endpoint}' uç noktasında %{s['error_rate']} oranında hata saptandı. Mimari stabilite risk altında.",
                            "evidence": s
                        })
                    
                    # Gecikme Denetimi
                    if s["avg_ms"] > self.threshold_latency_ms:
                        ops.append({
                            "id": f"api_lat_{self._generate_hash(endpoint + 'latency')}",
                            "category": "efficiency",
                            "source_type": "api_latency",
                            "severity": "medium",
                            "title": f"Düşük Performans: {endpoint}",
                            "description": f"'{endpoint}' uç noktası ortalama {s['avg_ms']}ms gecikme ile çalışıyor. Darboğaz optimizasyonu gerekiyor.",
                            "evidence": s
                        })
        except Exception as e:
            logger.error(f"API Audit failed: {e}")
        return ops

    async def _audit_watchdog_events(self) -> List[Dict[str, Any]]:
        """Watchdog üzerinden tekrarlanan hataları ve anomali paternlerini denetler."""
        ops = []
        try:
            patterns = await watchdog.search_events("tekrarlanan hata anomali timeout rate limit", top_k=15)
            agent_stats = {}
            for event in patterns:
                aid = event.get("agent_id")
                if aid:
                    agent_stats[aid] = agent_stats.get(aid, 0) + 1
            
            for aid, count in agent_stats.items():
                if count >= self.min_occurrences:
                    ops.append({
                        "id": f"wd_anomaly_{self._generate_hash(aid)}",
                        "category": "reliability",
                        "source_type": "recurring_anomaly",
                        "severity": "high",
                        "title": f"Tekrarlanan Ajan Hatası: {aid}",
                        "description": f"Ajan '{aid}' son operasyonlarda {count} kez anomali bildirdi. Davranışsal sapma detected.",
                        "evidence": {"agent_id": aid, "count": count}
                    })
        except Exception as e:
            logger.error(f"Watchdog Audit failed: {e}")
        return ops

    async def _audit_project_failures(self) -> List[Dict[str, Any]]:
        """Başarısız olan projeleri ve hata kök nedenlerini denetler."""
        ops = []
        try:
            async with AsyncSessionLocal() as db:
                recent_failures = await ProjectRepository.list_recent(db, limit=10, status="error")
                for proj in recent_failures:
                    ops.append({
                        "id": f"proj_fail_{self._generate_hash(str(proj.id))}",
                        "category": "reliability",
                        "source_type": "project_failure",
                        "severity": "high",
                        "title": f"Görev Başarısızlığı: {proj.title[:40]}",
                        "description": f"'{proj.title}' görevi başarısız oldu. Hata: {proj.error_detail[:150]}",
                        "evidence": {
                            "project_id": str(proj.id),
                            "error": proj.error_detail,
                            "agent": proj.assigned_agent
                        }
                    })
        except Exception as e:
            logger.error(f"Project Audit failed: {e}")
        return ops

    async def _audit_capacity_gaps(self) -> List[Dict[str, Any]]:
        """Sistemin yetenek matrisi ile gelen görev talepleri arasındaki boşlukları denetler."""
        ops = []
        try:
            # Mevcut uzman ajanları al
            agents = agency_loader.list_agents()
            agent_ids = {a["id"] for a in agents}
            
            # Son başarısız görevlerden "unsupported specialist" veya "missing tool" analizi yap
            # Bu kısım şimdilik statik bir kontrol, gelecekte LLM ile gap analizi yapılabilir.
            if "researcher" not in agent_ids:
                ops.append({
                    "id": "gap_researcher",
                    "category": "capacity",
                    "source_type": "missing_capability",
                    "severity": "medium",
                    "title": "Kapasite Eksikliği: Researcher",
                    "description": "Sistemde 'researcher' uzmanı bulunamadı. Derinlemesine araştırma görevleri sekteye uğrayabilir.",
                    "evidence": {"missing": "researcher"}
                })
        except Exception as e:
            logger.error(f"Capacity Audit failed: {e}")
        return ops

    def _generate_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:12]

sovereign_auditor = SovereignCortexAuditor()
