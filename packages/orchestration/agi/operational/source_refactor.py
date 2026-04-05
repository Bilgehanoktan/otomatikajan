import asyncio
import os
import json
import py_compile
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from packages.observability.logging import get_logger
from packages.persistence.session import session_scope
from packages.persistence.models import ImprovementOpportunity

_log = get_logger("agi_source_refactor")

class SourceRefactorNode:
    """
    Operasyonel Çekirdek - Kaynak Kod Refaktör Birimi (Source Refactor).
    Architect tarafından önerilen 'Bilişsel Refaktörleri' (Recursive Self-Engineering)
    otonom olarak uygular ve doğrular.
    """

    async def execute_pending_refactors(self):
        """Bekleyen kaynak kod refaktörlerini sırayla uygular."""
        _log.info("[SOURCE_REFACTOR] Bekleyen refaktörler kontrol ediliyor.")
        
        async with session_scope() as db:
            q = select(ImprovementOpportunity).where(
                ImprovementOpportunity.category == "code_quality",
                ImprovementOpportunity.status == "open"
            )
            result = await db.execute(q)
            pending = result.scalars().all()
            
            if not pending:
                _log.info("[SOURCE_REFACTOR] Uygulanacak bekleyen refaktör yok.")
                return

            for opp in pending:
                await self._process_refactor(db, opp)

    async def _process_refactor(self, db: AsyncSession, opp: ImprovementOpportunity):
        """Tek bir refaktör önerisini işler."""
        try:
            proposal = json.loads(opp.evidence_detail)
            agent_id = proposal.get("agent_id")
            new_code = proposal.get("suggested_refactor")
            
            if not agent_id or not new_code:
                _log.error(f"[SOURCE_REFACTOR] Geçersiz proposal formatı: {opp.id}")
                return

            target_path = f"agents/{agent_id}.py"
            if not os.path.exists(target_path):
                _log.error(f"[SOURCE_REFACTOR] Hedef dosya bulunamadı: {target_path}")
                return

            _log.info(f"[SOURCE_REFACTOR] Uygulanıyor: {agent_id} -> {target_path}")
            
            # 1. Yedek Al (Safety First)
            backup_path = f"{target_path}.bak"
            with open(target_path, "r", encoding="utf-8") as f:
                old_code = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(old_code)

            # 2. Yeni Kodu Yaz
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_code)

            # 3. Sözdizimi Kontrolü (Syntax Check)
            try:
                py_compile.compile(target_path, doraise=True)
                _log.info(f"[SOURCE_REFACTOR] Sözdizimi doğrulandı: {agent_id}")
                
                opp.status = "resolved"
                _log.info(f"[SOURCE_REFACTOR] Refaktör BAŞARIYLA TAMAMLANDI: {opp.id}")
            except Exception as syntax_err:
                _log.error(f"[SOURCE_REFACTOR] SÖZDİZİMİ HATASI! Geri alınıyor: {syntax_err}")
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(old_code)
                opp.status = "failed_syntax"

            await db.flush()

        except Exception as e:
            _log.error(f"[SOURCE_REFACTOR] Refaktör işleme hatası ({opp.id}): {e}")

# --- Background Task Definition ---
async def start_source_refactor_loop():
    from packages.orchestration.agi.monitoring.token_budgeter import token_budgeter
    node = SourceRefactorNode()
    
    while True:
        try:
            # ── ADAPTIVE SLEEP (Phase 24) ──
            health = await token_budgeter.check_health()
            score = health["health_score"]
            
            if score > 0.8:
                delay = 600  # 10 dk (Normal)
            elif score > 0.4:
                delay = 3600 # 1 saat (Stressed)
            else:
                delay = 14400 # 4 saat (Critical)
                _log.warning(f"[SOURCE_REFACTOR] Metabolizma kısıtlı, refaktör döngüsü yavaşlatıldı: {delay}s")

            await node.execute_pending_refactors()
            await asyncio.sleep(delay)
            
        except Exception as e:
            _log.error(f"[SOURCE_REFACTOR] Background loop error: {e}")
            await asyncio.sleep(60)
