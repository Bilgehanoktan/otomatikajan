import json
from typing import List, Dict, Any, Optional
from core.agi.schemas import ActionRecord, ContextPackage
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_compactor")

class ContextCompactor:
    """
    Cognitive Core: Context Management.
    Uzun aksiyon geçmişini özetleyerek token limitlerini korur ve bilişsel gürültüyü azaltır.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def compact(self, history: List[ActionRecord], current_goal: str) -> str:
        """
        Aksiyon geçmişini yüksek seviyeli bir özete dönüştürür.
        """
        if not history:
            return "Henüz bir işlem yapılmadı."

        _log.info(f"Bağlam sıkıştırılıyor: {len(history)} aksiyon işleniyor.")

        history_str = ""
        for i, rec in enumerate(history):
            status = "BAŞARILI" if rec.success else "BAŞARISIZ"
            history_str += f"{i+1}. Araç: {rec.tool_used} | Durum: {status} | Çıktı Özeti: {str(rec.output_data)[:200]}\n"

        prompt = f"""
        Şu ana kadar yapılan işlemleri ve ulaşılan durumu analiz et. 
        Görevin: {current_goal}
        
        İşlem Geçmişi:
        {history_str}
        
        Lütfen şu başlıklarla SIKIŞTIRILMIŞ bir bağlam özeti yap:
        1. Neler Başarıldı? (Kritik dosyalar, veriler, sonuçlar)
        2. Bilinen Engeller / Hatalar
        3. Şu anki durum (Neredeyiz?)
        4. Bir sonraki adım için kanıtlanmış ipuçları.
        
        Yanıtı kısa ve öz (max 500 kelime) tut.
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="analyst",
                prompt=prompt,
                system_prompt="Sen bir AGI Context Compactor bileşenisin. Görevin, karmaşık işlem geçmişini en saf ve yararlı haliyle özetlemektir."
            )
            return response.content
        except Exception as e:
            _log.error(f"Kompaktör hatası: {e}")
            return f"Bağlam sıkıştırma hatası, ham geçmişin son kısmı kullanılabilir. Hata: {str(e)}"

# Singleton
context_compactor = ContextCompactor()
