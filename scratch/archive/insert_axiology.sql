INSERT INTO sovereign_evidence (id, evidence_type, payload, created_at)
VALUES (
    'e6884674-884b-4663-8a35-645391696666', 
    'axiology_audit', 
    '{"decision": "ALLOW", "context": "Autonomous Scaling", "justification": "System resources are within nominal bounds.", "scores": {"ResourceIntegrity": 0.95, "OperationalRisk": 0.05}, "corrective_action": "None", "target_preview": "k8s-cluster-v2"}', 
    now()
);
