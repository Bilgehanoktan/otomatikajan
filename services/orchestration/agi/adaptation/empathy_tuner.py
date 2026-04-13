from typing import Optional
from services.observability.logging import get_logger
from services.orchestration.agi.cognitive.theory_of_mind import theory_of_mind

_log = get_logger("agi_empathy_tuner")

class EmpathyTuner:
    """
    Adaptation Core (Katman 30): Empathy Tuner.
    Kullanıcının psikolojik modeline göre sistemin ajan prompt'larını ('Kısa cevap ver', 
    'Ayrıntılı anlat', vb.) dinamik olarak yamalar.
    """
    def patch_system_prompt(self, base_prompt: str) -> str:
        """Kullanıcının mevcut zihinsel durumuna göre prompt'a empati / rezonans yaması ekler."""
        user_state = theory_of_mind.user_state
        patch = ""
        
        # Frustration
        if user_state.get("frustration", 0) > 0.7:
            patch += "\n[DİKKAT: Kullanıcı şu an gergin veya ardışık hatalarla uğraşıyor. Kesinlikle felsefe yapma. Özür dileme. Çok net kod ve çözüm ver. Tek cümleyle açıklama yap.]"
        
        # Urgency
        elif user_state.get("urgency", 0) > 0.6:
            patch += "\n[DİKKAT: Kullanıcı aceleci. Ayrıntılı teorik açıklamaları (eğer sormadıysa) atla. Sadece sonuç üret ve kodu/dosyayı ver.]"
            
        # Exploration
        elif user_state.get("exploration", 0) > 0.6:
            patch += "\n[DİKKAT: Kullanıcı keşif / öğrenme modunda. Kavramları derinlemesine neden-sonuç ilişkileriyle açıkla. Adım adım yürüt (Step-by-step).]"
            
        # Analytical
        elif user_state.get("analytical", 0) > 0.6:
            patch += "\n[DİKKAT: Kullanıcı analitik kod modunda. Mimari desenlere (Design Patterns), PEP-8 standartlarına ve best-practice'lere sıkı sıkıya uy.]"

        if patch:
            _log.info(f"Empathy Tuner: Prompt dinamik olarak yamalandı. (Sentezlenen User Mood: {theory_of_mind.get_inferred_state()})")
            return base_prompt + patch
            
        return base_prompt

# Singleton
empathy_tuner = EmpathyTuner()
