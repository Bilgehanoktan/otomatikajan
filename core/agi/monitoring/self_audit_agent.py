import os
import logging
import json
from typing import List, Dict, Any, Optional
from core.agi.operational.velocity_engine import velocity_engine
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from db.repository import ProjectRepository
from db.models import ProjectStatus
from db.session import session_scope

_log = logging.getLogger("agi_self_audit")

class SelfAuditAgent:
    """
    Autonomous Metabolism (Katman 7.8): Self-Audit Agent.
    Sistem kod tabanını otonom olarak tarar, teknik borçları ve "pass" bloklarını tespit eder.
    Tespit edilen sorunları CentralExecutive'in çözmesi için 'Self-Repair' görevlerine (Projects) dönüştürür.
    """

    def __init__(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        self.blocked_keywords = ["TODO", "FIXME", "pass  #", "except Exception: pass"]

    async def audit_and_remediate(self):
        """Otonom denetim ve iyileştirme döngüsü."""
        _log.info("--- OTONOM ÖZ-DENETİM (Self-Audit) BAŞLATILDI ---")
        
        # 1. Kod Tabanını Tara (Kritik Alanlar)
        issues = self._scan_for_technical_debt()
        
        if not issues:
            _log.info("[SELF-AUDIT] Kritik teknik borç saptanmadı.")
            return

        _log.info(f"[SELF-AUDIT] {len(issues)} teknik borç/eksiklik saptandı.")

        # 2. Issues Grupla ve Önceliklendir
        for issue in issues[:5]: # Token tasarrufu için ilk 5
            await self._create_remediation_project(issue)

        _log.info("--- OTONOM ÖZ-DENETİM TAMAMLANDI ---")

    def _scan_for_technical_debt(self) -> List[Dict[str, Any]]:
        findings = []
        target_dirs = ["core/agi", "agents", "api", "db", "llm"]
        
        for t_dir in target_dirs:
            full_path = os.path.join(self.root_dir, t_dir)
            if not os.path.exists(full_path):
                continue
            
            for root, _, files in os.walk(full_path):
                for file in files:
                    if not file.endswith(".py"):
                        continue
                        
                    f_path = os.path.join(root, file)
                    rel_path = os.path.relpath(f_path, self.root_dir).replace("\\", "/")
                    
                    try:
                        with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines):
                                for kw in self.blocked_keywords:
                                    if kw in line:
                                        findings.append({
                                            "file": rel_path,
                                            "line": i + 1,
                                            "content": line.strip(),
                                            "type": kw
                                        })
                    except Exception:
                        pass
        return findings

    async def _create_remediation_project(self, issue: Dict[str, Any]):
        """Tespit edilen hata/eksiklik için otonom bir iyileştirme projesi başlatır."""
        title = f"[SELF-REPAIR] Resolve '{issue['type']}' in {issue['file']}"
        description = (
            f"Otonom denetim sırasında {issue['file']} dosyasının {issue['line']}. satırında "
            f"kalan '{issue['content']}' eylemsizliği tespit edildi.\n\n"
            "GÖREV: Bu eksikliği modern AGI standartlarına (Faz 12.1) göre tamamla veya otonom hata yakalama ekle."
        )

        async with session_scope() as db:
            # Daha önce aynı dosya/satır için proje açılmış mı kontrolü
            existing = await ProjectRepository.list_recent(db, limit=1, search=title[:40])
            if existing:
                return

            _log.info(f"[SELF-AUDIT] İyileştirme projesi başlatılıyor: {title}")
            await ProjectRepository.create(
                db=db,
                title=title,
                description=description,
                source="self_audit",
                priority="low",
                tags=["self-repair", "tech-debt", "autonomous"],
                status=ProjectStatus.PENDING.value
            )
            await db.commit()

# Singleton
self_audit_agent = SelfAuditAgent()
