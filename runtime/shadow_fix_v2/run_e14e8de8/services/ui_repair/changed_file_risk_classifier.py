from typing import List, Dict, Any

class ChangedFileRiskClassifier:
    """
    Phase 5: Analyzes which files were changed and assigns a risk level.
    """
    
    CRITICAL_PATHS = [
        "libs/db/",
        "libs/auth/",
        "services/governance/",
        "libs/infra/"
    ]
    
    MEDIUM_PATHS = [
        "services/",
        "apps/refine_control_plane/src/middleware.ts",
        "apps/refine_control_plane/src/lib/api/"
    ]

    @staticmethod
    def classify(changed_files: List[str]) -> Dict[str, Any]:
        """
        Determines the risk level based on file paths.
        """
        risk_level = "LOW"
        risk_reasons = []
        
        for file_path in changed_files:
            if any(p in file_path for p in ChangedFileRiskClassifier.CRITICAL_PATHS):
                risk_level = "HIGH"
                risk_reasons.append(f"Critical system file modified: {file_path}")
            elif any(p in file_path for p in ChangedFileRiskClassifier.MEDIUM_PATHS):
                if risk_level != "HIGH":
                    risk_level = "MEDIUM"
                risk_reasons.append(f"Sensitive service file modified: {file_path}")
                
        if not risk_reasons:
            risk_reasons.append("Only frontend UI components modified.")
            
        return {
            "risk_level": risk_level,
            "reasons": risk_reasons
        }
