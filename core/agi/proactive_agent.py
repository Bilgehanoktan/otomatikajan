import asyncio
import os
import sys
from typing import List, Dict, Any, Optional
from observability.logging import get_logger

_log = get_logger("agi_proactive_agent")

class ProactiveAgent:
    """
    Super-Intelligence Layer (Katman 12): Proactive Mission Control.
    Sistemin dış girdi beklemek yerine kendi hedeflerini (Curiosity) otonom olarak belirlediği katman.
    """
    def __init__(self, interval_s: int = 3600):
        self.interval_s = interval_s
        self.is_running = False

    async def heartbeat(self):
        """
        Süreklilik Döngüsü: Periyodik olarak sistem sağlığını, mimariyi ve yetenekleri denetler.
        """
        _log.info(f"AGI Proaktif Kalp Atışı (Heartbeat) başladı. Periyot: {self.interval_s}s")
        self.is_running = True
        
        from db.session import session_scope
        
        while self.is_running:
            try:
                async with session_scope() as db:
                    # --- BÜTÜNLEŞİK BİLİNÇ DÖNGÜSÜ (UNIFIED MIND CYCLE) [Katman 27] ---
                    from core.agi.consciousness.integrated_orchestrator import integrated_orchestrator
                    _log.info("Bütünleşik AGI Zihin Döngüsü (Unified Mind Cycle) başlatılıyor...")
                    await integrated_orchestrator.run_mind_cycle(db)
                    # -------------------------------------------------------------------
                    
                # 5. Bekle
                await asyncio.sleep(self.interval_s)
                
            except Exception as e:
                _log.error(f"Proaktif Döngü Hatası: {e}")
                await asyncio.sleep(60) # Hata durumunda kısa bekleme

    def stop(self):
        self.is_running = False

# --- Singleton ---
proactive_agent = ProactiveAgent()
