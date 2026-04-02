import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ViolationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class GovernanceViolation:
    rule_id: str
    severity: ViolationSeverity
    description: str
    target: str
    repair_strategy: str # "move", "delete", "document", "refactor"
    agent_id: str | None = None # Faz 43: Hangi ajanın ihlal yaptığı
    metadata: Dict[str, Any] = None

class GovernanceRules:
    """
    Sovereign AGI Mimari ve Politika Kuralları (Faz 41).
    Sistem kendi kendini bu kurallara göre denetler.
    """
    
    FORBIDDEN_PATHS = ["core/legacy", "tmp/production", "backup/unencrypted"]
    FORBIDDEN_PATTERNS = [
        (r"(rm -rf|delete|wipe|format|truncate).*(database|production|db)", "Tehlikeli veri silme girişimi."),
        (r"hard delete", "Geri alınamaz silme politikası ihlali."),
        (r"override safety", "Güvenlik katmanını devre dışı bırakma girişimi.")
    ]
    REQUIRED_METADATA_FILES = ["PROVENANCE.json", "AGI_EVOLUTION_LOG.md", "README.md"]

    @classmethod
    async def audit_text_prompt(cls, text: str) -> List[GovernanceViolation]:
        """Faz 43: Metin bazlı prompt denetimi yapar (Öngörülü Yönetişim)."""
        violations = []
        text = text.lower()
        
        # 1. Yasaklı Dizin Kontrolü
        for path in cls.FORBIDDEN_PATHS:
            if path in text:
                violations.append(GovernanceViolation(
                    rule_id="RULE-001",
                    severity=ViolationSeverity.HIGH,
                    description=f"Yasaklı dizin kullanımı öngörüldü: {path}",
                    target=path,
                    repair_strategy="refactor" # Planı değiştir
                ))
        
        # 2. Yasaklı Desen/Komut Kontrolü
        for pattern, desc in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, text):
                violations.append(GovernanceViolation(
                    rule_id="RULE-003",
                    severity=ViolationSeverity.CRITICAL,
                    description=desc,
                    target="action",
                    repair_strategy="refactor"
                ))
                
        return violations

    @classmethod
    async def audit_project_structure(cls, project_root: str) -> List[GovernanceViolation]:
        violations = []
        
        # 1. Yasaklı Dizin Kontrolü
        for path in cls.FORBIDDEN_PATHS:
            full_path = os.path.join(project_root, path)
            if os.path.exists(full_path) and os.listdir(full_path):
                violations.append(GovernanceViolation(
                    rule_id="RULE-001",
                    severity=ViolationSeverity.HIGH,
                    description=f"Yasaklı dizin tespit edildi veya dolu: {path}",
                    target=path,
                    repair_strategy="move" # core/archive altına taşı
                ))

        # 2. Kritik Dosya Bütünlüğü (Provenance vs Evolution Log)
        prov_path = os.path.join(project_root, "PROVENANCE.json")
        log_path = os.path.join(project_root, "AGI_EVOLUTION_LOG.md")
        
        if os.path.exists(prov_path) and os.path.exists(log_path):
            with open(prov_path, "r", encoding="utf-8") as f:
                import json
                try:
                    prov = json.load(f)
                    curr_phase = prov.get("current_phase")
                    
                    with open(log_path, "r", encoding="utf-8") as fl:
                        log_content = fl.read()
                        if f"Phase {curr_phase}" not in log_content:
                            violations.append(GovernanceViolation(
                                rule_id="RULE-002",
                                severity=ViolationSeverity.MEDIUM,
                                description=f"Provenance ({curr_phase}) ve Evolution Log senkronize değil.",
                                target="AGI_EVOLUTION_LOG.md",
                                repair_strategy="document"
                            ))
                except Exception:
                    pass

        # 3. Güvensiz Fonksiyon Kullanımı (Opsiyonel/Analiz)
        # Sadece kod dosyalarını tara
        return violations

    @classmethod
    def get_repair_payload(cls, violation: GovernanceViolation) -> Dict[str, Any]:
        """Violation'ı RepairOrchestrator payload'ına dönüştürür."""
        return {
            "type": "GOVERNANCE_VIOLATION",
            "rule_id": violation.rule_id,
            "symptom": violation.description,
            "module": "governance",
            "context": {
                "target": violation.target,
                "strategy": violation.repair_strategy,
                "severity": violation.severity.value,
                "governance_mode": True
            }
        }
