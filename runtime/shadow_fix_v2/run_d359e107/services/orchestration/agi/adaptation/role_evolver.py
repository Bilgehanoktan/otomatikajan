import json
import os
from typing import List, Dict, Any, Optional
from services.observability.logging import get_logger

_log = get_logger("agi_role_evolver")

class RoleEvolver:
    """
    Adaptation Core (Katman 22): Role Evolver.
    Otonom olarak system prompt kütüphanesini ve ajan kimliklerini evrimleştirir.
    """
    def __init__(self, model_orch: Optional[Any] = None, roles_path: str = "core/agi/roles/specialists.json"):
        self.model_orch = model_orch
        self.roles_path = roles_path

    async def evolve_roles(self, new_specialist: Dict[str, Any]) -> bool:
        """
        Sentezlenen yeni uzmanı sisteme kalıcı olarak ekler.
        """
        if not new_specialist:
            return False
            
        _log.info(f"Ajan Kimliği Evrimleştiriliyor (Role Evolution): {new_specialist.get('id')}...")
        
        # 1. Uzmanlar dosyasını yükle veya oluştur
        os.makedirs(os.path.dirname(self.roles_path), exist_ok=True)
        roles = {}
        if os.path.exists(self.roles_path):
            try:
                with open(self.roles_path, "r", encoding="utf-8") as f:
                    roles = json.load(f)
            except Exception:
                roles = {}

        # 2. Yeni uzmanı ekle
        role_id = new_specialist.get("id", "auto_specialist")
        roles[role_id] = new_specialist.get("raw", "{}")
        
        # 3. Dosyaya kaydet
        with open(self.roles_path, "w", encoding="utf-8") as f:
            json.dump(roles, f, indent=2)
            
        _log.info(f"Otonom Uzman Kayıt Edildi: {role_id}")
        
        # 4. Orkestratörün bu rolleri görmesini sağla (reload logical)
        return True

# Singleton
role_evolver = RoleEvolver()
