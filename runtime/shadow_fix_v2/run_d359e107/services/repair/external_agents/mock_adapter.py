from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.repair.external_agents.base import ExternalAgentAdapter
from services.repair.external_agents.models import ExternalAgentContext, ExternalAgentResult


class MockExternalAgentAdapter(ExternalAgentAdapter):
    def __init__(self) -> None:
        self.last_agent_dir: Path = Path("repair_outputs") / "default" / "external_agents" / self.agent_key

    @property
    def agent_key(self) -> str:
        return "swe_agent"

    @property
    def supported_modes(self) -> list[str]:
        return ["local_adapter", "reference_only"]

    def validate_context(self, context: ExternalAgentContext) -> None:
        if context.agent_key != self.agent_key:
            raise ValueError(f"Context agent_key '{context.agent_key}' does not match adapter '{self.agent_key}'")
        if context.requested_mode not in self.supported_modes:
            raise ValueError(f"Mode '{context.requested_mode}' is not supported by '{self.agent_key}'")

    def run(self, context: ExternalAgentContext) -> ExternalAgentResult:
        self.validate_context(context)
        
        output_root = Path(context.output_dir) if context.output_dir else Path("repair_outputs")
        output_dir = output_root / context.incident_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        agent_dir = output_dir / "external_agents" / self.agent_key
        agent_dir.mkdir(parents=True, exist_ok=True)
        self.last_agent_dir = agent_dir
        
        # 1. input_artifact.json
        input_data = {
            "incident_id": context.incident_id,
            "repair_case_id": context.repair_case_id,
            "requested_mode": context.requested_mode,
            "allowed_tools": context.allowed_tools,
            "forbidden_actions": context.forbidden_actions,
            "workspace_policy": context.workspace_policy,
            "risk_limit": context.risk_limit,
        }
        (agent_dir / "input_artifact.json").write_text(json.dumps(input_data, indent=2), encoding="utf-8")
        
        # 2. patch_candidate.diff
        fake_diff = (
            "--- a/services/repair/mock_dummy.py\n"
            "+++ b/services/repair/mock_dummy.py\n"
            "@@ -1,3 +1,3 @@\n"
            "-def mock(): pass\n"
            "+def mock(): return 'fixed'\n"
        )
        patch_file = agent_dir / "patch_candidate.diff"
        patch_file.write_text(fake_diff, encoding="utf-8")
        
        # 3. external_agent_trace.json
        fake_trace = {
            "steps": [
                {"step": 1, "action": "search", "query": "mock_dummy.py"},
                {"step": 2, "action": "replace", "file": "services/repair/mock_dummy.py"}
            ]
        }
        (agent_dir / "external_agent_trace.json").write_text(json.dumps(fake_trace, indent=2), encoding="utf-8")
        
        # 4. risk_notes.json
        fake_risk = {
            "analyzed_paths": ["services/repair/mock_dummy.py"],
            "risk_score": 0.1,
            "constitution_violations": []
        }
        (agent_dir / "risk_notes.json").write_text(json.dumps(fake_risk, indent=2), encoding="utf-8")
        
        result = ExternalAgentResult(
            status="COMPLETED",
            candidate_source=self.agent_key,
            output_artifact=str(patch_file),
            confidence_score=0.9,
            evidence_refs=[
                str(agent_dir / "external_agent_trace.json"),
                str(agent_dir / "risk_notes.json")
            ],
            cost=0.01,
            duration_ms=450.0,
            risk="low",
            warnings=[],
            blocked_reason=None
        )
        
        self.build_artifacts(result)
        return result

    def build_artifacts(self, result: ExternalAgentResult) -> dict[str, Any]:
        self.last_agent_dir.mkdir(parents=True, exist_ok=True)
        result_data = result.to_dict()
        (self.last_agent_dir / "external_agent_result.json").write_text(
            json.dumps(result_data, indent=2, default=str), encoding="utf-8"
        )
        return result_data
