import os
import psutil
import gc
import time
import logging
from typing import Dict, Any, List, Callable
from threading import Lock

# Loglama yapılandırması (Geleneksel)
logger = logging.getLogger("memory_governor")

class MemoryGovernor:
    """
    Sistemin bellek (RAM) tüketen yapılarını denetleyen ve 'Otonom Pruning' 
    (Budama) işlemlerini yürüten merkezi servis.
    Faz 30: Unified Galactic Cortex (UGC) ile uyumlu.
    """
    
    def __init__(self, limit_mb: float = 1024.0, warning_mb: float = 800.0):
        self.MAX_MEMORY_MB = float(os.getenv("MAX_MEMORY_MB", limit_mb))
        self.WARNING_MEMORY_MB = float(os.getenv("WARNING_MEMORY_MB", warning_mb))
        self._registry: List[Callable] = []  # Temizlik fonksiyonları listesi
        self._lock = Lock()
        self._last_cleanup = 0.0
        
        logger.info(f"[MEM-GOV] Başlatıldı. Sınır: {self.MAX_MEMORY_MB}MB, Uyarı: {self.WARNING_MEMORY_MB}MB")

    def register_cleanup_callback(self, callback: Callable):
        """Hafıza tasarrufu gerektiğinde çağrılacak fonksiyonu kaydeder."""
        with self._lock:
            if callback not in self._registry:
                self._registry.append(callback)
                logger.debug(f"[MEM-GOV] Yeni temizlik callback'i eklendi: {callback.__name__ if hasattr(callback, '__name__') else str(callback)}")

    def get_current_usage_mb(self) -> float:
        """Sürecin RSS bellek kullanımını MB cinsinden döner."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    async def audit_and_prune(self, force: bool = False):
        """
        Bellek kullanımını denetler ve gerekirse 'Pruning' işlemlerini tetikler.
        """
        usage = self.get_current_usage_mb()
        
        # 1. Eğer kullanım uyarı sınırının altındaysa ve force değilse geç
        if not force and usage < self.WARNING_MEMORY_MB:
            return

        # 2. Kritik Durum veya Uyarı Durumu
        action_level = "CRITICAL" if usage >= self.MAX_MEMORY_MB else "WARNING"
        logger.warning(f"[MEM-GOV] Bellek Kullanımı {action_level}: {usage:.2f}MB. Temizlik başlatılıyor...")

        # 3. Kayıtlı tüm bileşenleri temizle (In-memory deques, cache, vb.)
        with self._lock:
            for callback in self._registry:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"[MEM-GOV] Temizlik hatası ({callback}): {e}")

        # 4. Manuel Garbage Collection
        gc.collect()
        
        # 5. Sonuç Raporu
        new_usage = self.get_current_usage_mb()
        saved = usage - new_usage
        logger.info(f"[MEM-GOV] Temizlik tamamlandı. Son kullanım: {new_usage:.2f}MB. Kurtarılan: {saved:.2f}MB")
        self._last_cleanup = time.time()

    async def monitor_loop(self, interval_s: int = 60):
        """Arka plan izleme döngüsü."""
        while True:
            try:
                await self.audit_and_prune()
            except Exception as e:
                logger.error(f"[MEM-GOV] Monitor hatası: {e}")
            
            import asyncio
            await asyncio.sleep(interval_s)

# Singleton Instance
memory_governor = MemoryGovernor()
