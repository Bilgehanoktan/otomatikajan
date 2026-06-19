from typing import Tuple
from apps.bilgeapi.schemas.incident import IncidentResponse
from apps.bilgeapi.schemas.diagnostic import DiagnosticResult

class RiskScoringService:
    def calculate_risk(self, incident: IncidentResponse, diagnostic: DiagnosticResult) -> Tuple[float, str]:
        factors = []
        score = 0.0

        # 1. Environment Weight
        env = incident.environment.lower()
        if env == "production":
            score += 0.3
            factors.append("environment is production (+0.30)")
        elif env == "staging":
            score += 0.1
            factors.append("environment is staging (+0.10)")
        else:
            score += 0.05
            factors.append(f"environment is {env} (+0.05)")

        # 2. Severity Weight
        sev = incident.severity.lower()
        if sev == "critical":
            score += 0.4
            factors.append("incident severity is critical (+0.40)")
        elif sev == "high":
            score += 0.3
            factors.append("incident severity is high (+0.30)")
        elif sev == "medium":
            score += 0.2
            factors.append("incident severity is medium (+0.20)")
        else:
            score += 0.1
            factors.append(f"incident severity is {sev} (+0.10)")

        # 3. Incident Kind Weight
        kind = incident.kind.lower()
        if "security" in kind or "auth" in kind:
            score += 0.2
            factors.append(f"incident kind '{incident.kind}' indicates security/auth concerns (+0.20)")
        elif "db" in kind or "database" in kind or "corruption" in kind:
            score += 0.2
            factors.append(f"incident kind '{incident.kind}' indicates database concerns (+0.20)")
        elif "leak" in kind or "outage" in kind:
            score += 0.15
            factors.append(f"incident kind '{incident.kind}' indicates resource leak/outage concerns (+0.15)")
        else:
            score += 0.05
            factors.append(f"incident kind is {incident.kind} (+0.05)")

        # 4. Confidence (Uncertainty adds to risk)
        conf = diagnostic.confidence if diagnostic.confidence is not None else 1.0
        uncertainty = (1.0 - conf) * 0.1
        if uncertainty > 0.0:
            score += uncertainty
            factors.append(f"diagnostic uncertainty is {uncertainty:.2f} (confidence={conf:.2f})")

        # 5. Recommendation analysis
        db_keywords = ["migration", "postgres", "sql", "db", "reindex", "database", "query", "connection"]
        sec_keywords = ["secret", "key", "token", "ssl", "cert", "permission", "auth", "credential", "password", "tls"]
        crit_keywords = ["delete", "drop", "truncate", "remove", "wipe", "flush", "destroy"]
        workflow_keywords = ["checkout", "payment", "order", "dispatch", "cron", "queue", "workflow"]

        has_db = False
        has_sec = False
        has_crit = False
        has_wf = False

        recs = diagnostic.recommendations
        for r in recs:
            desc = ""
            if isinstance(r, dict):
                desc = r.get("description", "").lower()
            elif hasattr(r, "description"):
                desc = getattr(r, "description", "").lower()

            if any(kw in desc for kw in db_keywords):
                has_db = True
            if any(kw in desc for kw in sec_keywords):
                has_sec = True
            if any(kw in desc for kw in crit_keywords):
                has_crit = True
            if any(kw in desc for kw in workflow_keywords):
                has_wf = True

        if has_crit:
            score += 0.3
            factors.append("recommendation contains critical destructive action (delete/drop) (+0.30)")
        if has_sec:
            score += 0.25
            factors.append("recommendation contains security-sensitive change (+0.25)")
        if has_db:
            score += 0.2
            factors.append("recommendation contains database operation (+0.20)")
        if has_wf:
            score += 0.15
            factors.append("recommendation contains critical workflow operation (+0.15)")

        # Final score bounding
        final_score = max(0.0, min(1.0, score))
        reason = "Risk score is " + f"{final_score:.2f}" + ". Factors: " + ", ".join(factors)
        return round(final_score, 2), reason
