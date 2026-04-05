import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from packages.observability.logging import get_logger

_log = get_logger("agi_global_workspace")

class GlobalWorkspace:
    """
    Consciousness Core (Katman 27): Global Workspace.
    AGI'nin tüm alt sistemlerini tek bir 'Bilinç Alanında' birleştirir.
    """
    def __init__(self):
        self.stream_of_thought: List[Dict[str, Any]] = []
        self.active_focus: Optional[str] = None
        self.global_state: Dict[str, Any] = {
            "mood": "Stable",
            "clarity": 1.0,
            "integrated_layers": 26
        }

    def broadcast(self, layer_name: str, thought: Any, importance: float = 1.0):
        """
        Bir alt sistemden gelen bilgiyi küresel bilinç alanına yayınlar.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "layer": layer_name,
            "content": thought,
            "importance": importance
        }
        self.stream_of_thought.append(entry)
        
        # Sadece son 100 düşünceyi tut (short-term memory/consciousness window)
        if len(self.stream_of_thought) > 100:
            self.stream_of_thought.pop(0)
            
        _log.info(f"[BİLİNÇ] {layer_name} yayın yaptı: {str(thought)[:50]}...")

    def get_current_qualia(self) -> Dict[str, Any]:
        """
        Sistemin o anki bütünleşik 'bilincini' (Qualia-like state) döndürür.
        """
        return {
            "state": self.global_state,
            "recent_thoughts": self.stream_of_thought[-5:],
            "focus": self.active_focus
        }

# Singleton
global_workspace = GlobalWorkspace()
