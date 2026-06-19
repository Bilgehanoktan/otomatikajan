from typing import Dict, List, Any, Tuple
from libs.db.models.governance_models import GovernorDomain, GovernorConflictType

class GovernorConflictResolver:
    """
    Farklı domain governor'ların kararları arasındaki çakışmaları çözer.
    """

    def detect_conflicts(self, domain_decisions: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        conflicts = []
        domains = list(domain_decisions.keys())
        
        for i in range(len(domains)):
            for j in range(i + 1, len(domains)):
                d1_name = domains[i]
                d2_name = domains[j]
                d1 = domain_decisions[d1_name]
                d2 = domain_decisions[d2_name]
                
                # Karar çakışması kontrolü
                if d1["recommended_decision"] != d2["recommended_decision"]:
                    # Eğer biri NO_ACTION ise genelde çakışma sayılmaz, ama risk farkı olabilir
                    if d1["recommended_decision"] == "NO_ACTION" or d2["recommended_decision"] == "NO_ACTION":
                        continue
                    
                    conflict_type = self._classify_conflict(d1, d2)
                    if conflict_type != GovernorConflictType.NONE:
                        conflicts.append({
                            "domain_a": d1_name,
                            "domain_b": d2_name,
                            "decision_a": d1["recommended_decision"],
                            "decision_b": d2["recommended_decision"],
                            "conflict_type": conflict_type,
                            "summary": f"{d1_name} wants {d1['recommended_decision']}, while {d2_name} wants {d2['recommended_decision']}"
                        })
        return conflicts

    def _classify_conflict(self, d1: Dict[str, Any], d2: Dict[str, Any]) -> GovernorConflictType:
        # Eğer kararlar tamamen farklıysa
        if d1["recommended_decision"] != d2["recommended_decision"]:
            return GovernorConflictType.ACTION_DISAGREEMENT
        
        # Eğer risk sınıfları çok farklıysa
        # (Burada risk_score üzerinden bir karşılaştırma yapılabilir)
        if abs(d1["risk_score"] - d2["risk_score"]) > 300:
            return GovernorConflictType.RISK_DISAGREEMENT
            
        return GovernorConflictType.NONE

    def resolve(self, decisions: Dict[str, Dict[str, Any]], conflicts: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Çakışmaları öncelik kurallarına göre çözer ve final kararı döner.
        """
        from services.governance.governor_policy_config import GovernorPolicyConfig
        applied_constraints = []
        
        # Faz 9: Politika tabanlı öncelik sırasını al
        priority_order = GovernorPolicyConfig.get_veto_priority_order()
        
        # 1. POLICY VETO (Config enabled ise)
        if GovernorPolicyConfig.is_policy_veto_enabled() and "POLICY" in decisions:
            policy = decisions["POLICY"]
            if policy["recommended_decision"] in ("REQUIRES_PRIME_REVIEW", "REQUIRES_QUORUM"):
                applied_constraints.append("POLICY_ENFORCED_RESTRICTION")
                return policy, applied_constraints

        # 2. Öncelik listesine göre domain'leri kontrol et
        for domain_name in priority_order:
            if domain_name in decisions:
                decision = decisions[domain_name]
                # Eğer domain yüksek risk bildiriyorsa (eskalasyon istiyorsa), öncelik ona geçer
                if decision["recommended_decision"] in ("REQUIRES_PRIME_REVIEW", "REQUIRES_QUORUM"):
                    applied_constraints.append(f"{domain_name}_PRIORITY_VETO")
                    return decision, applied_constraints

        # 3. Varsayılan: En yüksek riskli/muhafazakar kararı seç
        sorted_decisions = sorted(decisions.values(), key=lambda x: x["risk_score"], reverse=True)
        return sorted_decisions[0], applied_constraints
