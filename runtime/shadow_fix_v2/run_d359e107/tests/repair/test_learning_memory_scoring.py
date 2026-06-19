from __future__ import annotations

import json
from pathlib import Path
import pytest
import shutil

from services.repair.learning_memory_scoring import (
    record_repair_outcome,
    load_strategy_success_profile,
    update_strategy_success_profile,
    score_candidates_with_memory
)

@pytest.fixture
def temp_output_root(tmp_path):
    output_dir = tmp_path / "repair_outputs"
    output_dir.mkdir()
    yield output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_outcome_profile_flow(temp_output_root):
    agent_key = "test_agent"
    strategy = "test_strategy"
    
    # 1. Start with no history
    profile = load_strategy_success_profile(agent_key, strategy, output_root=temp_output_root)
    assert profile["total_attempts"] == 0
    assert profile["successful_attempts"] == 0
    assert profile["historical_success_score"] == 0.0
    
    # 2. Record a successful outcome
    outcome1 = {
        "incident_id": "INC-1",
        "run_id": "RUN-1",
        "finding_id": "FIND-1",
        "selected_candidate_id": "cand-1",
        "candidate_source": "test_generator",
        "agent_key": agent_key,
        "strategy": strategy,
        "decision": "approve_and_apply",
        "human_gate_status": "APPROVED",
        "risk_score": 0.20,
        "risk_prediction_accuracy": None,
        "test_result": "passed",
        "post_decision_result": "draft_pr_ready",
        "operator_rationale": "Perfect outcome",
    }
    
    profile1 = update_strategy_success_profile(agent_key, strategy, outcome1, output_root=temp_output_root)
    assert profile1["total_attempts"] == 1
    assert profile1["successful_attempts"] == 1
    assert profile1["historical_success_score"] == 1.0
    assert profile1["last_result"] == "success"
    
    # 3. Record a failed outcome
    outcome2 = outcome1.copy()
    outcome2["run_id"] = "RUN-2"
    outcome2["test_result"] = "failed"
    outcome2["human_gate_status"] = "REJECTED"
    outcome2["post_decision_result"] = "rejected"
    
    profile2 = update_strategy_success_profile(agent_key, strategy, outcome2, output_root=temp_output_root)
    assert profile2["total_attempts"] == 2
    assert profile2["successful_attempts"] == 1
    assert profile2["failed_attempts"] == 1
    assert profile2["historical_success_score"] == 0.5
    assert profile2["last_result"] == "failed"


def test_score_candidates_insufficient_history(temp_output_root):
    candidates = [{
        "candidate_id": "cand-insufficient",
        "agent_key": "new_agent",
        "strategy": "conservative",
        "base_score": 0.80,
    }]
    
    scored = score_candidates_with_memory(
        candidates,
        incident_id="INC-INSUF",
        run_id="RUN-INSUF",
        output_root=temp_output_root
    )
    
    assert len(scored) == 1
    assert scored[0]["memory_adjustment"] == 0.0
    assert scored[0]["final_score"] == 0.80
    assert "Insufficient history" in scored[0]["explanation"]


def test_score_candidates_positive_adjustments(temp_output_root):
    agent_key = "expert_agent"
    strategy = "expert_strategy"
    
    # Simulate 4 attempts, all successful (success_score = 1.0)
    for i in range(4):
        outcome = {
            "incident_id": f"INC-EXP-{i}",
            "run_id": f"RUN-EXP-{i}",
            "finding_id": "FIND-EXP",
            "selected_candidate_id": "cand-exp",
            "candidate_source": "test_generator",
            "agent_key": agent_key,
            "strategy": strategy,
            "decision": "approve_and_apply",
            "human_gate_status": "APPROVED",
            "risk_score": 0.10,
            "risk_prediction_accuracy": None,
            "test_result": "passed",
            "post_decision_result": "draft_pr_ready",
            "operator_rationale": "High quality",
        }
        update_strategy_success_profile(agent_key, strategy, outcome, output_root=temp_output_root)
        
    candidates = [{
        "candidate_id": "cand-exp",
        "agent_key": agent_key,
        "strategy": strategy,
        "base_score": 0.70,
    }]
    
    scored = score_candidates_with_memory(
        candidates,
        incident_id="INC-EXP-TEST",
        run_id="RUN-EXP-TEST",
        output_root=temp_output_root
    )
    
    assert len(scored) == 1
    # Clamps to max 0.10 adjustment
    assert scored[0]["memory_adjustment"] == 0.10
    assert scored[0]["final_score"] == 0.80
    assert "Historical success bonus" in scored[0]["explanation"]


def test_score_candidates_safety_gates(temp_output_root):
    agent_key = "safety_agent"
    strategy = "safety_strategy"
    
    # 1. Policy denied candidate: adjustment MUST be -0.10 (strict penalty)
    candidates = [{
        "candidate_id": "cand-denied",
        "agent_key": agent_key,
        "strategy": strategy,
        "base_score": 0.85,
        "policy_denied": True,
        "blocked_reason": "Denied due to import policy"
    }]
    
    scored = score_candidates_with_memory(
        candidates,
        incident_id="INC-SAFE-1",
        run_id="RUN-SAFE-1",
        output_root=temp_output_root
    )
    assert scored[0]["memory_adjustment"] == -0.10
    assert scored[0]["final_score"] == 0.75
    assert "Policy denied" in scored[0]["explanation"]
    
    # 2. Sandbox failed candidate: adjustment must not be positive, gets -0.05
    candidates2 = [{
        "candidate_id": "cand-sandbox-failed",
        "agent_key": agent_key,
        "strategy": strategy,
        "base_score": 0.85,
        "sandbox_failed": True
    }]
    
    scored2 = score_candidates_with_memory(
        candidates2,
        incident_id="INC-SAFE-2",
        run_id="RUN-SAFE-2",
        output_root=temp_output_root
    )
    assert scored2[0]["memory_adjustment"] <= 0.0
    assert scored2[0]["final_score"] <= 0.85
    assert "Sandbox failed" in scored2[0]["explanation"]
