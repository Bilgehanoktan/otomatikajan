import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("core.skill_catalog")

try:
    import frontmatter
except ImportError:
    frontmatter = None


def _load_skill_metadata(file_obj):
    if frontmatter is not None:
        return frontmatter.load(file_obj).metadata

    content = file_obj.read()
    if not content.startswith("---"):
        return {}

    _, metadata_block, _ = content.split("---", 2)
    metadata = {}
    for line in metadata_block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata

@dataclass
class SkillDescriptor:
    skill_id: str
    name: str
    description: str
    path: str
    metadata: Dict[str, any]

class SkillCatalog:
    """
    SKILL.md dosyalarından metadata okuyan ve yöneten katalog sınıfı.
    """
    def __init__(self, skills_dir: str = ".agents/skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, SkillDescriptor] = {}
        self._load_catalog()

    def _load_catalog(self):
        """Kataloğu tarar ve yükler."""
        if not os.path.exists(self.skills_dir):
            logger.warning(f"⚠️ Skill kataloğu bulunamadı: {self.skills_dir}")
            return

        for root, dirs, files in os.walk(self.skills_dir):
            if "SKILL.md" in files:
                skill_path = os.path.join(root, "SKILL.md")
                try:
                    with open(skill_path, 'r', encoding='utf-8') as f:
                        metadata = _load_skill_metadata(f)
                        skill_id = os.path.basename(root)
                        name = metadata.get('name', skill_id)
                        description = metadata.get('description', '')
                        
                        self.skills[skill_id] = SkillDescriptor(
                            skill_id=skill_id,
                            name=name,
                            description=description,
                            path=skill_path,
                            metadata=metadata
                        )
                        logger.debug(f"✅ Skill yüklendi: {skill_id}")
                except Exception as e:
                    logger.error(f"❌ Skill yükleme hatası ({skill_path}): {e}")

        logger.info(f"📚 Skill kataloğu yüklendi: {len(self.skills)} skill aktif.")

    def get_skill(self, skill_id: str) -> Optional[SkillDescriptor]:
        return self.skills.get(skill_id)

    def list_skills(self) -> List[SkillDescriptor]:
        return list(self.skills.values())

    def find_skills_by_context(self, context_text: str) -> List[str]:
        """
        Bağlam metnine göre uygun skill_id'leri döner.
        Basit anahtar kelime eşleşmesi yapar.
        """
        selected = []
        context_lower = context_text.lower()
        for skill_id, descriptor in self.skills.items():
            # Skill name veya description içinde geçiyorsa seç
            if skill_id.lower() in context_lower or \
               descriptor.name.lower() in context_lower or \
               descriptor.description.lower() in context_lower:
                selected.append(skill_id)
        return selected

    def get_skill_summary(self, skill_id: str) -> str:
        """Prompt içine gömülmek üzere sıkıştırılmış özet döner."""
        skill = self.get_skill(skill_id)
        if not skill:
            return ""
        return f"- **{skill.name}**: {skill.description}"

# Singleton
skill_catalog = SkillCatalog()
