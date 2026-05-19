
import os
import yaml
import json

base_path = "benchmarks/repair_bench/cases"

new_cases = [
    {
        "id": "re-004-rbac-drift",
        "incident_id": "INC-2024-04-14-04",
        "module": "services.governance.iam",
        "title": "RBAC Policy Drift in Regional Clusters",
        "description": "Critical permissions missing in US-WEST-1 after federation sync failure.",
        "risk_class": "high",
        "cost_class": "low",
        "target_behavior": "policy_convergence",
        "verification_profile": {"governance": "strict", "federation": "required"},
        "input_context": {"drift_detected": True, "affected_region": "us-west-1", "missing_roles": ["admin_override"]},
        "expected_signals": {"convergence_score": 1.0}
    },
    {
        "id": "re-005-memory-leak",
        "incident_id": "INC-2024-04-14-05",
        "module": "libs.workflow.executor",
        "title": "Slow Memory Leak in Long-Running Tasks",
        "description": "Workflow executor consumes 10MB/hour due to signal listener leakage.",
        "risk_class": "medium",
        "cost_class": "medium",
        "target_behavior": "heap_stability",
        "verification_profile": {"regression": "intensive", "chaos": "required"},
        "input_context": {"leak_detected": True, "heap_growth_rate": "10MB/hr"},
        "expected_signals": {"heap_growth_delta": 0.0}
    },
    {
        "id": "re-006-quorum-loss",
        "incident_id": "INC-2024-04-14-06",
        "module": "libs.mesh.consensus",
        "title": "Consensus Quorum Loss Under High Latency",
        "description": "Raft protocol fails to elect leader when inter-region latency > 500ms.",
        "risk_class": "critical",
        "cost_class": "low",
        "target_behavior": "leader_election",
        "verification_profile": {"mesh": "strict", "chaos": "high_latency"},
        "input_context": {"latency_ms": 600, "quorum_loss": True},
        "expected_signals": {"leader_active": True}
    },
    {
        "id": "re-007-api-contract-break",
        "incident_id": "INC-2024-04-14-07",
        "module": "services.workflow_api.internal",
        "title": "Breaking Change in Internal Workflow API",
        "description": "New field required in request but not passed by legacy observers.",
        "risk_class": "medium",
        "cost_class": "low",
        "target_behavior": "backward_compatibility",
        "verification_profile": {"build": "strict", "regression": "full"},
        "input_context": {"api_error": "400 Bad Request", "missing_field": "x-trace-id"},
        "expected_signals": {"compat_mode": "active"}
    },
    {
        "id": "re-008-db-deadlock",
        "incident_id": "INC-2024-04-14-08",
        "module": "libs.db.transaction",
        "title": "Concurrent Transaction Deadlock in Multi-Agent Sync",
        "description": "Two agents updating same metadata key result in deadlock during high-concurrency loops.",
        "risk_class": "medium",
        "cost_class": "low",
        "target_behavior": "deadlock_avoidance",
        "verification_profile": {"regression": "concurrency", "ops": "strict"},
        "input_context": {"deadlock_count": 5, "affected_table": "agent_metadata"},
        "expected_signals": {"deadlock_rate": 0.0}
    },
    {
        "id": "re-009-token-exhaustion",
        "incident_id": "INC-2024-04-14-09",
        "module": "services.improve.generator",
        "title": "LLM Token Quota Exhaustion",
        "description": "Repair engine stops working when global OpenAI/Gemini quota is exhausted for the hour.",
        "risk_class": "low",
        "cost_class": "low",
        "target_behavior": "graceful_degradation",
        "verification_profile": {"economic": "strict", "ops": "fallback"},
        "input_context": {"quota_remaining": 0, "fallback_active": False},
        "expected_signals": {"local_model_active": True}
    },
    {
        "id": "re-010-alert-fatigue",
        "incident_id": "INC-2024-04-14-10",
        "module": "services.observability.alerting",
        "title": "Spamming Alerts During Service Mesh Flapping",
        "description": "Alert manager sends 500+ Slack messages in 2 minutes during network instability.",
        "risk_class": "low",
        "cost_class": "low",
        "target_behavior": "alert_throttling",
        "verification_profile": {"ops": "strict", "chaos": "network_flap"},
        "input_context": {"alert_rate": "250/min", "network_flapping": True},
        "expected_signals": {"throttled_rate_max": 5}
    }
]

for case in new_cases:
    path = os.path.join(base_path, case["id"])
    os.makedirs(path, exist_ok=True)
    
    # case.yaml
    case_yaml = {
        "incident_id": case["incident_id"],
        "module": case["module"],
        "title": case["title"],
        "description": case["description"],
        "risk_class": case["risk_class"],
        "cost_class": case["cost_class"],
        "target_behavior": case["target_behavior"],
        "verification_profile": case["verification_profile"]
    }
    with open(os.path.join(path, "case.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(case_yaml, f)
        
    # input_context.json
    with open(os.path.join(path, "input_context.json"), "w", encoding="utf-8") as f:
        json.dump(case["input_context"], f, indent=2)
        
    # expected_signals.json
    with open(os.path.join(path, "expected_signals.json"), "w", encoding="utf-8") as f:
        json.dump(case["expected_signals"], f, indent=2)

print("Generated 7 more benchmark cases.")
