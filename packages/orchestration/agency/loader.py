import os
try:
    import frontmatter
except ImportError:
    class frontmatter:
        @staticmethod
        def load(path):
            class _Doc:
                metadata = {}
                content = ""
            return _Doc()
        @staticmethod
        def loads(text):
            class _Doc:
                metadata = {}
                content = text
            return _Doc()
from typing import Dict, List, Any, Optional
from packages.observability.logging import get_logger

_log = get_logger("core.agency.loader")

class AgencyLoader:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.agents: Dict[str, Dict[str, Any]] = {}

    def load_agents(self):
        self.agents = {}
        if not os.path.exists(self.base_dir):
            _log.warning(f"Agency base directory not found: {self.base_dir}")
            return

        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(".md") and "README" not in file.upper() and "CONTRIBUTING" not in file.upper():
                    file_path = os.path.join(root, file)
                    self._load_agent(file_path)
        
        dynamic_dir = os.path.join(self.base_dir, "dynamic")
        if os.path.exists(dynamic_dir):
            for file in os.listdir(dynamic_dir):
                if file.endswith(".md"):
                    self._load_agent(os.path.join(dynamic_dir, file))
                    
        _log.info(f"Loaded {len(self.agents)} specialist agents.")

    def _load_agent(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
                base_name = os.path.basename(file_path)
                parent_dir = os.path.basename(os.path.dirname(file_path))
                
                # If the filename is generic (SKILL.md), use the directory name as the ID
                if base_name.upper() == "SKILL.MD":
                    agent_id = parent_dir
                else:
                    agent_id = os.path.splitext(base_name)[0]
                
                category = parent_dir if agent_id != parent_dir else os.path.basename(os.path.dirname(os.path.dirname(file_path)))
                self.agents[agent_id] = {
                    "id": agent_id,
                    "name": post.get("name", agent_id.replace("-", " ").title()),
                    "description": post.get("description", ""),
                    "system_prompt": getattr(post, "content", ""),
                    "category": category,
                    "file_path": file_path,
                    "capabilities": post.get("capabilities", []) if isinstance(post.get("capabilities"), list) else [],
                    "preferred_task_types": post.get("preferred_task_types", []) if isinstance(post.get("preferred_task_types"), list) else [],
                    "risk_level": post.get("risk_level", "medium"),
                    **getattr(post, "metadata", {})
                }
        except Exception as e:
            _log.debug(f"Error loading agent {file_path}: {e}")

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        # Faz 12.4: Otonom Yükleme Tetikleyici
        if not self.agents:
            self.load_agents()
        return list(self.agents.values())

    def find_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        return [
            agent for agent in self.agents.values()
            if capability in agent.get("capabilities", [])
        ]

    @property
    def personas(self) -> Dict[str, Dict[str, Any]]:
        return self.agents

# Faz 12.4: Bilişsel Bütünlük — Otonom Loader Senkronizasyonu
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
default_path = os.path.join(_root, "packages", "orchestration", "agi", "agents", "agency_library")
fallback_path = os.path.join(_root, "external", "vendor", "deer-flow", "skills", "public")

if not os.path.exists(default_path) and os.path.exists(fallback_path):
    _log.info(f"AgencyLoader falling back to: {fallback_path}")
    base_path = fallback_path
else:
    base_path = default_path

agency_loader = AgencyLoader(base_path)

def get_agency_loader() -> AgencyLoader:
    global agency_loader
    if not agency_loader.agents:
        agency_loader.load_agents()
    return agency_loader
