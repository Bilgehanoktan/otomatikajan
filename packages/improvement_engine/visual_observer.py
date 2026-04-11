import os
import aiofiles
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class VisualUXObserver:
    """
    Sovereign AGI (Faz 12.1) Görsel Denetim Birimi.
    Sistemin frontend dosyalarını tarayarak UI/UX iyileştirme fırsatları sunar.
    Başlangıçta taslak (Stub) olan bu modül artık gerçek tarama mantığıyla çalışmaktadır.
    """
    
    def __init__(self, db=None, model_orch=None):
        self.db = db
        self.model_orch = model_orch
        self.scan_targets = [
            "apps/dashboard/index.html",
            "apps/dashboard/css/sovereign_v121.css",
            "apps/dashboard/css/style_v2.css",
            "dashboard/index.html",
            "apps/api/static/dashboard/index.html", # fallback paths
            "apps/api/static/style.css"
        ]
        # Gerçek dosya yollarını doğrula
        self.active_targets = []
        for t in self.scan_targets:
            if os.path.exists(t):
                self.active_targets.append(t)
            else:
                # Root seviyesindeki dashboard
                alt_t = os.path.join(os.getcwd(), t)
                if os.path.exists(alt_t):
                    self.active_targets.append(alt_t)

    async def scan(self) -> List[Dict[str, Any]]:
        findings = []
        
        if not self.active_targets:
            logger.warning("VisualUXObserver: No dashboard files found for scanning.")
            return []

        # 1. Dashboard ve CSS dosyalarını oku
        for target in self.active_targets:
            try:
                async with aiofiles.open(target, mode='r', encoding='utf-8') as f:
                    content = await f.read()
                    
                # ModelOrchestrator ile analiz et
                if self.model_orch:
                    prompt = f"""
                    Aşağıdaki {os.path.basename(target)} dosyasını (Sovereign AGI Dashboard parçası) UI/UX ve performans açısından analiz et. 
                    Herhangi bir eksiklik (örneğin: mobile responsiveness, z-index hataları, eksik animasyonlar, 
                    gereksiz stub alanları) bulursan bunları JSON formatında bir liste olarak döndür.
                    
                    Yanıt sadece JSON olmalı.
                    Alanlar: 
                    - title: Kısa başlık.
                    - description: İyileştirme detaylı anlatımı.
                    - severity: high, medium, low.
                    - category: ui_ux, performance, accessibility.
                    
                    Kod Snippet (ilk 5000 karakter):
                    {content[:5000]}
                    """
                    
                    try:
                        # architect agent'ını kullanarak analiz et
                        response = await self.model_orch.complete_task(
                            agent_role="architect",
                            prompt=prompt,
                            system_prompt="Sen bir Premium UI/UX Denetçisisin. Modern web standartlarına (Glassmorphism, Neon, Responsive) hakimsin."
                        )
                        
                        import json
                        import re
                        json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
                        if json_match:
                            llm_findings = json.loads(json_match.group())
                            for lf in llm_findings:
                                lf["source_type"] = "visual_scan"
                                lf["source_ref"] = f"{os.path.basename(target)}_{lf.get('category', 'ui')}"
                                findings.append(lf)
                    except Exception as llm_err:
                        logger.error(f"VisualUXObserver LLM analysis failed: {llm_err}")

                # 2. Hardened Heuristics (Kural tabanlı kontroller)
                if target.endswith(".css") or ".css" in target:
                    if "sovereign-neon" not in content:
                        findings.append({
                            "source_type": "visual_scan",
                            "source_ref": f"{os.path.basename(target)}_neon",
                            "title": "Upgrade Component Glow Effects",
                            "description": "The current CSS lacks 'sovereign-neon' class for premium glassmorphism glow. This should be added to main container.",
                            "severity": "medium",
                            "category": "ui_ux",
                            "evidence": f"Missing glow class in {target}"
                        })
                
                if "TODO" in content or "FIXME" in content or "TASK_STUB" in content:
                    findings.append({
                        "source_type": "visual_scan",
                        "source_ref": f"{os.path.basename(target)}_todo",
                        "title": f"Resolve UI Debt in {os.path.basename(target)}",
                        "description": "There are pending TODO/FIXME markers in the frontend source that need address before production.",
                        "severity": "low",
                        "category": "ui_ux",
                        "evidence": f"Found markers in {target}"
                    })
                    
            except Exception as e:
                logger.error(f"VisualUXObserver failed to scan {target}: {e}")

        # Eğer hiçbir şey bulamazsa ama dosyalar varsa (ve model yoksa) bir baz line öneri ekle
        if not findings and self.active_targets:
             findings.append({
                "source_type": "visual_scan",
                "source_ref": "dashboard_base_check",
                "title": "Verify UI Component Isolation",
                "description": "System verified the presence of dashboard components. Next: verify if all JS modules are pre-loaded to prevent layout shift.",
                "severity": "low",
                "category": "performance",
                "evidence": "Verification run: dashboard present."
            })
            
        return findings
