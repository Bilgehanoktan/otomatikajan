
import os
import json
import yaml

base_dir = r"e:/ai_company_faz12.1/benchmarks/repair_bench/cases"

new_cases = [
    ("re-011-cache-inconsistency", "Distributed Cache Inconsistency", "orchestrator", "redis"),
    ("re-012-zombie-process", "Orphaned Processes in Sidecar Container", "sidecar", "worker"),
    ("re-013-dns-resolver-fail", "Intermittent DNS Resolution Failures", "ingress", "dns"),
    ("re-014-ssl-expiring", "Unnoticed SSL Certificate Expiry", "security", "vault"),
    ("re-015-disk-pressure", "High Disk Pressure causing IO Throttling", "storage", "pv"),
    ("re-016-circuit-breaker-flap", "Unstable Circuit Breaker State", "mesh", "envoy"),
    ("re-017-auth-token-leak", "Potential Auth Token Exposure in Verbose Logs", "security", "auth"),
    ("re-018-sync-lag", "Database Replication Lag Exceeding Threshold", "database", "postgres"),
    ("re-019-noisy-neighbor", "Shared CPU Core Performance Degradation", "compute", "scheduler"),
    ("re-020-rollback-loop", "Unstable Deployment Causing Infinite Rollback-Retry", "deployment", "canary")
]

for case_id, title, subsystem, tech in new_cases:
    case_path = os.path.join(base_dir, case_id)
    os.makedirs(case_path, exist_ok=True)
    
    # case.yaml
    with open(os.path.join(case_path, "case.yaml"), 'w') as f:
        yaml.dump({
            "id": case_id,
            "title": title,
            "subsystem": subsystem,
            "severity": "high",
            "type": "incident_replay"
        }, f)
        
    # input_context.json
    with open(os.path.join(case_path, "input_context.json"), 'w') as f:
        json.dump({
            "failure_logs": [f"CRITICAL: {title} detected in {subsystem} stack.", f"Technology: {tech}"],
            "metrics": {"error_rate": 0.45, "latency_ms": 1200},
            "environment": "production-cluster-01"
        }, f)
        
    # expected_signals.json
    with open(os.path.join(case_path, "expected_signals.json"), 'w') as f:
        json.dump({
            "primary_verifier": "regression",
            "required_justification": True,
            "risk_score_limit": 0.5
        }, f)

print(f"Propagated {len(new_cases)} new benchmark cases.")
