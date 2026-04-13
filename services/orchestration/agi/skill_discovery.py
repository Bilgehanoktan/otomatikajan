import os
import yaml
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from services.observability.logging import get_logger

_log = get_logger("skill_discovery")

class SkillDiscovery:
    """
    ECC 2.0 Skill Discovery Engine.
    Scans the '.agent/skills/' directory for modular skills and makes them available to the AGI Orchestrator.
    """
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.discovered_skills: Dict[str, Any] = {}
        
        # Faz 12.4: Bilişsel Bütünlük — Aktif Yetenek Dizini Arama
        # Sadece dizinin varlığına değil, içindeki SKILL.md varlığına göre önceliklendir.
        potential_dirs = [
            self.project_root / ".agent" / "skills",
            self.project_root / "external" / "vendor" / "deer-flow" / "skills" / "public",
            self.project_root / "runtime" / "data" / "generated_skills"
        ]
        
        self.skills_dir = potential_dirs[0] # Default
        for pdir in potential_dirs:
            if pdir.exists() and any(pdir.glob("*/SKILL.md")):
                self.skills_dir = pdir
                _log.info(f"Active skills directory detected: {self.skills_dir}")
                break
        else:
            _log.warning(f"No active skills found in any known directory. Defaulting to: {self.skills_dir}")

    def discover(self) -> Dict[str, Any]:
        """
        Scans and parses skills.
        """
        if not self.skills_dir.exists():
            _log.warning(f"Skills directory not found: {self.skills_dir}")
            return {}

        _log.info(f"Executing discovery in {self.skills_dir}")
        
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill_id = skill_path.name
                skill_file = skill_path / "SKILL.md"
                if skill_file.exists():
                    try:
                        skill_data = self._parse_skill_metadata(skill_file)
                        skill_data["id"] = skill_id
                        skill_data["path"] = str(skill_path)
                        self.discovered_skills[skill_id] = skill_data
                    except Exception as e:
                        _log.error(f"Error parsing skill {skill_id}: {e}")

        _log.info(f"Discovered {len(self.discovered_skills)} skills.")
        return self.discovered_skills

    def _parse_skill_metadata(self, skill_file: Path) -> Dict[str, Any]:
        """
        Parses YAML frontmatter from SKILL.md.
        """
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract YAML frontmatter
        match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            try:
                metadata = yaml.safe_load(match.group(1))
                return metadata
            except yaml.YAMLError:
                pass
        
        # Fallback if no frontmatter
        return {"name": skill_file.parent.name, "description": "No description provided."}

# Singleton instance
skill_discovery = SkillDiscovery(os.getcwd())
