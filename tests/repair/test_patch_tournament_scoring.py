import json
import shutil
import tempfile
from pathlib import Path
import pytest

from services.repair.patch_tournament_models import PatchTournamentWeights, ScoreBreakdown
from services.repair.patch_tournament import (
    normalize_candidate_scores,
    evaluate_candidate_eligibility,
    score_patch_candidate,
    rank_patch_candidates,
    run_patch_tournament
)

@pytest.fixture
def temp_output_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_weighted_scoring_formula_sums_expected_score():
    # Setup candidate with normal metrics
    candidate = {
        "candidate_id": "cand-1",
        "policy_status": "approved",
        "diff": "some-diff",
        "base_score": 0.80,
        "security_score": 0.90,
        "maintainability_score": 0.85,
        "rollback_safety_score": 0.80,
        "cognitive_integrity_score": 0.90,
        "historical_success_score": 0.75,
        "cost_score": 0.95,
        "memory_adjustment": 0.05
    }
    
    inputs = {
        "sandbox_result": {"cand-1": {"tests_passed": True, "patch_applied": True}},
        "risk_report": {"risk_score": 0.20, "blast_radius": "low"},
        "cognitive_integrity": {"cognitive_integrity_score": 0.90},
        "candidate_memory_score": {}
    }
    
    weights = PatchTournamentWeights()
    breakdown = normalize_candidate_scores(candidate, inputs)
    
    # Calculate base expected score using weights:
    # test_score: 1.0 * 0.20 = 0.20
    # build_score: 1.0 * 0.10 = 0.10
    # risk_score: (1 - 0.20) = 0.80 * 0.15 = 0.12
    # security_score: 0.90 * 0.15 = 0.135
    # maintainability_score: 0.85 * 0.10 = 0.085
    # rollback_safety_score: 0.80 * 0.10 = 0.08
    # cognitive_integrity_score: 0.90 * 0.10 = 0.09
    # historical_success_score: 0.75 * 0.05 = 0.0375
    # cost_score: 0.95 * 0.03 = 0.0285
    # blast_radius_score: 1.0 * 0.02 = 0.02  (blast_radius low gives 1.0)
    # Sum: 0.20 + 0.10 + 0.12 + 0.135 + 0.085 + 0.08 + 0.09 + 0.0375 + 0.0285 + 0.02 = 0.896
    # With memory_adjustment: 0.896 + 0.05 = 0.946 -> rounded to 0.9460
    
    final_score = score_patch_candidate(candidate, breakdown, weights, inputs)
    assert abs(final_score - 0.9460) < 0.001

def test_policy_denied_candidate_is_disqualified():
    candidate = {
        "candidate_id": "cand-1",
        "policy_status": "DENIED",
        "diff": "some-diff"
    }
    inputs = {}
    breakdown = normalize_candidate_scores(candidate, inputs)
    eligible, reasons = evaluate_candidate_eligibility(candidate, breakdown, inputs)
    assert not eligible
    assert "policy_status == 'DENIED'" in reasons

def test_sandbox_failed_candidate_is_disqualified():
    candidate = {
        "candidate_id": "cand-1",
        "policy_status": "approved",
        "diff": "some-diff"
    }
    inputs = {
        "sandbox_result": {
            "cand-1": {
                "tests_passed": False,
                "patch_applied": True
            }
        }
    }
    breakdown = normalize_candidate_scores(candidate, inputs)
    eligible, reasons = evaluate_candidate_eligibility(candidate, breakdown, inputs)
    assert not eligible
    assert "sandbox_status == 'failed'" in reasons or breakdown.test_score == 0.0

def test_security_below_threshold_is_disqualified():
    candidate = {
        "candidate_id": "cand-1",
        "policy_status": "approved",
        "diff": "some-diff",
        "security_score": 0.40
    }
    inputs = {}
    breakdown = normalize_candidate_scores(candidate, inputs)
    eligible, reasons = evaluate_candidate_eligibility(candidate, breakdown, inputs)
    assert not eligible
    assert "security_score < 0.50" in reasons[0]

def test_memory_score_is_used_when_available():
    candidate = {
        "candidate_id": "cand-1",
        "diff": "some-diff",
    }
    inputs = {
        "candidate_memory_score": {
            "candidate_scores": [
                {
                    "candidate_id": "cand-1",
                    "historical_success_score": 0.90,
                    "memory_adjustment": 0.08
                }
            ]
        }
    }
    breakdown = normalize_candidate_scores(candidate, inputs)
    assert breakdown.historical_success_score == 0.90
    
    weights = PatchTournamentWeights()
    final_score = score_patch_candidate(candidate, breakdown, weights, inputs)
    # Check that adjustment is applied
    # Without adjustment base is computed, check that final includes the +0.08 adjustment
    base_score = score_patch_candidate(candidate, breakdown, weights, {})
    assert abs(final_score - min(1.0, base_score + 0.08)) < 0.001

def test_missing_memory_score_defaults_to_neutral():
    candidate = {
        "candidate_id": "cand-1",
        "diff": "some-diff"
    }
    inputs = {}
    breakdown = normalize_candidate_scores(candidate, inputs)
    assert breakdown.historical_success_score == 0.50

def test_rank_patch_candidates_selects_highest_eligible_score():
    candidates = [
        {
            "candidate_id": "cand-1",
            "policy_status": "approved",
            "diff": "some-diff",
            "base_score": 0.60
        },
        {
            "candidate_id": "cand-2",
            "policy_status": "approved",
            "diff": "some-diff",
            "base_score": 0.85
        },
        {
            "candidate_id": "cand-3",
            "policy_status": "DENIED",
            "diff": "some-diff",
            "base_score": 0.99
        }
    ]
    inputs = {}
    weights = PatchTournamentWeights()
    ranked = rank_patch_candidates(candidates, inputs, weights)
    
    assert len(ranked) == 3
    # First is cand-2 (highest eligible score)
    assert ranked[0].candidate_id == "cand-2"
    assert ranked[0].eligible
    # Second is cand-1
    assert ranked[1].candidate_id == "cand-1"
    assert ranked[1].eligible
    # Third is cand-3 (disqualified)
    assert ranked[2].candidate_id == "cand-3"
    assert not ranked[2].eligible

def test_all_candidates_disqualified_returns_no_selection(temp_output_dir):
    candidates = [
        {
            "candidate_id": "cand-1",
            "policy_status": "DENIED",
            "diff": "some-diff"
        }
    ]
    
    # Write patch_candidates.json
    run_dir = temp_output_dir / "INC-1" / "taskflow" / "RUN-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "patch_candidates.json").write_text(json.dumps(candidates))
    
    result = run_patch_tournament("INC-1", "RUN-1", output_root=temp_output_dir)
    assert result.selected_candidate_id is None
    assert len(result.candidates) == 1
    assert not result.candidates[0].eligible

def test_tournament_result_artifact_is_written(temp_output_dir):
    candidates = [
        {
            "candidate_id": "cand-1",
            "policy_status": "approved",
            "diff": "some-diff",
            "base_score": 0.75
        }
    ]
    
    run_dir = temp_output_dir / "INC-1" / "taskflow" / "RUN-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "patch_candidates.json").write_text(json.dumps(candidates))
    
    result = run_patch_tournament("INC-1", "RUN-1", output_root=temp_output_dir)
    
    result_file = run_dir / "tournament_result.json"
    assert result_file.exists()
    
    data = json.loads(result_file.read_text(encoding="utf-8"))
    assert data["incident_id"] == "INC-1"
    assert data["run_id"] == "RUN-1"
    assert data["selected_candidate_id"] == "cand-1"
