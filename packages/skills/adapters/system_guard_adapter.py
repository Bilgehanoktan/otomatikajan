from packages.skills.base import BaseSkillAdapter, SkillRequest, SkillResult
from packages.orchestration.governance.safety_gate import safety_gate

class SystemGuardSkillAdapter(BaseSkillAdapter):
    skill_id = "system_guard"

    def can_handle(self, req: SkillRequest) -> bool:
        text = f"{req.title} {req.description}".lower()
        return any(k in text for k in ["freeze", "guard", "unfreeze", "protect", "kilit", "dondur"])

    async def execute(self, req: SkillRequest) -> SkillResult:
        """
        GStack /freeze ve /unfreeze komutlarini otonom olarak yonetir.
        """
        try:
            mode = "freeze" if any(k in req.description.lower() for k in ["freeze", "dondur", "kilit"]) else "unfreeze"
            
            # Context'ten veya description'dan dosya yollarini ayikla
            files = req.context.get("files", [])
            if not files and "dosya:" in req.description.lower():
                 # Basit ayiklama: "dosya: main.py, config.json"
                 import re
                 match = re.search(r"dosya:\s*([^\s]+)", req.description.lower())
                 if match:
                     files = [f.strip() for f in match.group(1).split(",")]

            if not files:
                 return SkillResult(
                     success=False,
                     skill_id=self.skill_id,
                     summary="Freeze/Unfreeze islemi icin hedef dosya belirtilmedi."
                 )

            results = []
            for f in files:
                if mode == "freeze":
                    safety_gate.freeze(f)
                    results.append(f"{f} [FROZEN] - Koruma altina alindi.")
                else:
                    safety_gate.unfreeze(f)
                    results.append(f"{f} [UNFROZEN] - Koruma kaldirildi.")

            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                summary=f"Sistem Guvenligi Guncellendi: {len(files)} dosya.",
                data={"results": results, "mode": mode}
            )

        except Exception as e:
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                summary=f"Guard Hatasi: {str(e)}"
            )
