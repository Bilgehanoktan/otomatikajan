import os
from datetime import datetime
from typing import Any

from skills.base import BaseSkillAdapter, SkillRequest, SkillResult


class StrategicPlanningSkillAdapter(BaseSkillAdapter):
    skill_id = "strategic_planning"

    def can_handle(self, req: SkillRequest) -> bool:
        text = f"{req.title} {req.description}".lower()
        return any(k in text for k in ["plan", "design doc", "strategi", "ceo-review", "architect", "tasarim"])

    async def execute(self, req: SkillRequest) -> SkillResult:
        """
        GStack /plan-ceo-review mantigiyla bir stratejik plan veya tasarim dokumani uretir.
        """
        try:
            from packages.orchestration.model_orchestrator import model_orchestrator
            
            prompt = f"""
Sen DeerFlow Otonom Yazılım Şirketi'nin Baş Mimarı ve Strateji Sorumlusu (CSO) rolündesin.
Aşağıdaki görev için GStack standartlarında kapsamlı bir Tasarım Dökümanı (Design Doc) hazırlaman gerekiyor.

BAŞLIK: {req.title}
GÖREV: {req.description}
PROJE ID: {req.project_id or 'adhoc'}

Döküman şu bölümleri içermelidir:
1. **YÖNETİCİ ÖZETİ**: Ne yapılacak ve neden önemli?
2. **KAPSAM VE SINIRLAR**: Ne dahil, ne değil?
3. **TEKNİK MİMARİ**: Hangi bileşenler etkilenecek?
4. **KRİTİK RİSKLER**: Neler yanlış gidebilir (GStack /guard mantığıyla)?
5. **UYGULAMA ADIMLARI**: Sırasıyla yapılacak işler.

Dili profesyonel, yapıcı ve teknik olarak detaylı (Turkish) olmalıdır.
"""
            # ModelOrchestrator'ı kullanarak tasarım dokümanı üret
            response = await model_orchestrator.generate(
                prompt=prompt,
                model_hint="gpt-4o", # Yüksek kaliteli model önerisi
                task_id=f"plan-{req.project_id or 'adhoc'}"
            )

            # Dökümanı bir dosya olarak da kaydedelim (opsiyonel)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            doc_dir = os.path.join(os.getcwd(), "docs", "plans")
            os.makedirs(doc_dir, exist_ok=True)
            doc_path = os.path.join(doc_dir, f"design_{timestamp}.md")
            
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(response)

            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                summary=f"Stratejik Tasarım Dökümanı üretildi: {doc_path}",
                data={
                    "design_doc": response,
                    "file_path": doc_path,
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                summary=f"Stratejik planlama hatası: {str(e)}",
            )
