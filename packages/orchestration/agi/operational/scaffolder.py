import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from packages.observability.logging import get_logger

_log = get_logger("agi_scaffolder")

class Scaffolder:
    """
    Mimari planları fiziksel dosya yapılarına dönüştüren 'Yapısal İnşacı' düğümü.
    Yeni modüller, katmanlar ve standart iskeletler (boilerplate) oluşturur.
    """
    
    def __init__(self, project_root: str | None = None):
        if project_root:
            self.root = Path(project_root).resolve()
        else:
            self.root = Path(__file__).resolve().parents[3]

    def scaffold_subsystem(self, proposal_action: Dict[str, Any]) -> bool:
        """
        Yeni bir alt sistem iskeleti oluşturur.
        Örn: {"type": "create_subsystem", "path": "core/services/", "files": ["base.py", "__init__.py"]}
        """
        target_path = self.root / proposal_action["path"]
        
        # 1. Güvenlik ve Geçerlilik Kontrolü
        if not self._is_path_safe(target_path):
            _log.error(f"[SCAFFOLDER] Güvenli olmayan dizin yolu: {target_path}")
            return False
            
        try:
            # 2. Dizinleri Oluştur
            os.makedirs(target_path, exist_ok=True)
            _log.info(f"[SCAFFOLDER] Dizin oluşturuldu: {target_path}")
            
            # 3. Dosyaları/İskeletleri Oluştur
            files = proposal_action.get("files_to_scaffold", ["__init__.py"])
            for filename in files:
                file_path = target_path / filename
                if not file_path.exists():
                    self._create_boilerplate(file_path, filename)
                    _log.info(f"[SCAFFOLDER] Dosya iskeleti yazıldı: {file_path}")
                else:
                    _log.warning(f"[SCAFFOLDER] Dosya zaten mevcut: {file_path}")
                    
            return True
        except Exception as e:
            _log.error(f"[SCAFFOLDER] Scaffolding hatası: {e}")
            return False

    def split_file_structure(self, source_path: str, targets: List[str]) -> bool:
        """
        Dev bir dosyanın bölünmesi için hedef dosyaları (iskeletleri) oluşturur.
        Not: Kodun taşınması 'Developer' ajanının görevidir.
        """
        try:
            for t in targets:
                target_path = self.root / t
                if not target_path.exists():
                    os.makedirs(target_path.parent, exist_ok=True)
                    target_path.touch()
                    _log.info(f"[SCAFFOLDER] Bölme hedefi oluşturuldu: {target_path}")
            return True
        except Exception as e:
            _log.error(f"[SCAFFOLDER] File split structure hatası: {e}")
            return False

    def _create_boilerplate(self, path: Path, filename: str):
        """Standardize edilmiş boilerplate içeriği yazar."""
        content = f'"""\n{filename} - Faz 19 Otonom Mimari İskeleti.\n'
        content += f'Oluşturulma Tarihi: {os.uname().nodename if hasattr(os, "uname") else "System"}\n"""\n\n'
        
        if filename.endswith(".py"):
            content += "from packages.observability.logging import get_logger\n\n"
            content += f"logger = get_logger('{path.stem}')\n\n"
            content += "class Placeholder:\n    pass\n"
            
        path.write_text(content, encoding="utf-8")

    def _is_path_safe(self, path: Path) -> bool:
        """Kritik dizinlerin (git, gemini, venv) korunması."""
        forbidden = {".git", ".gemini", "node_modules", ".venv", "venv"}
        parts = path.parts
        return not any(f in parts for f in forbidden)

# --- Singleton Export ---
scaffolder = Scaffolder()
