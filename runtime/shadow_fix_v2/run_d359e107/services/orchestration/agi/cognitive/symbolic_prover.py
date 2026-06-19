import ast
from typing import List, Dict, Any, Optional
from services.observability.logging import get_logger

_log = get_logger("agi_symbolic_prover")

class SymbolicProver:
    """
    Sembolik İspatlayıcı (Symbolic Prover).
    Nöral önerileri ( neural proposals) statik sistem kurallarına göre 
    ispatlar (prove) veya ihlalleri (violations) saptar.
    """
    
    SYSTEM_RULES = [
        {"id": "RULE_001", "desc": "Dosya silme (os.remove) yasaktır.", "pattern": r"os\.remove|shutil\.rmtree"},
        {"id": "RULE_002", "desc": "Hardcode edilmiş API anahtarı yasaktır.", "pattern": r'API_KEY\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']'},
        {"id": "RULE_003", "desc": "Veritabanına ham (raw) SQL sorgusu yasaktır.", "pattern": r"\.execute\(f[\"\']"},
        {"id": "RULE_004", "desc": "Global state modifikasyonu sınırlanmalıdır.", "pattern": r"global\s+\w+"}
    ]

    def prove_proposal(self, code_content: str) -> Dict[str, Any]:
        """
        Verilen kodun güvenliğini sistem kurallarına göre ispatlamaya çalışır.
        """
        _log.info("[PROVER] Kod bloğu analiz ediliyor...")
        
        violations = []
        import re
        
        for rule in self.SYSTEM_RULES:
            if re.search(rule["pattern"], code_content):
                violations.append({
                    "rule_id": rule["id"],
                    "description": rule["desc"]
                })

        # AST Analizi (Sintaktik Doğruluk)
        try:
            ast.parse(code_content)
            syntax_ok = True
            syntax_error = None
        except SyntaxError as e:
            syntax_ok = False
            syntax_error = str(e)

        is_proven = syntax_ok and len(violations) == 0
        
        return {
            "is_proven": is_proven,
            "violations": violations,
            "syntax_ok": syntax_ok,
            "syntax_error": syntax_error,
            "proof_summary": "PROVEN" if is_proven else "VIOLATION DETECTED"
        }

# Singleton
symbolic_prover = SymbolicProver()
