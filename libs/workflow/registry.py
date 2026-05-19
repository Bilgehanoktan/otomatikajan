"""
libs/workflow/registry.py — Phase 13.04
Central registry for workflow types and their required execution steps.
"""
from typing import Any

from pydantic import BaseModel


class WorkflowStepTemplate(BaseModel):
    id: str
    action: str
    description: str
    depends_on: list[str] = []
    condition: str | None = None
    config: dict[str, Any] = {}

class WorkflowDefinition(BaseModel):
    type: str # e.g., "feature_dev", "bug_fix", "refactor"
    steps: list[WorkflowStepTemplate]

class WorkflowRegistry:
    """Registry that maps workflow types to their step sequences."""

    _definitions: dict[str, WorkflowDefinition] = {}

    @classmethod
    def register(cls, definition: WorkflowDefinition):
        cls._definitions[definition.type] = definition

    @classmethod
    def get_definition(cls, workflow_type: str) -> WorkflowDefinition:
        if workflow_type not in cls._definitions:
            # Return a simple default/fallback if not registered
            return WorkflowDefinition(
                type=workflow_type,
                steps=[
                    WorkflowStepTemplate(
                        id="plan",
                        action="cognitive_plan",
                        description="Analyze and plan sequence"
                    ),
                    WorkflowStepTemplate(
                        id="execute",
                        action="operational_execute",
                        description="Execute primary task",
                        depends_on=["plan"]
                    )
                ]
            )
        return cls._definitions[workflow_type]

# Initial/Core Registrations
WorkflowRegistry.register(
    WorkflowDefinition(
        type="default",
        steps=[
            WorkflowStepTemplate(id="plan", action="plan_subtasks", description="Plan project subtasks"),
            WorkflowStepTemplate(id="execute", action="execute_subtasks", description="Execute planned subtasks", depends_on=["plan"]),
            WorkflowStepTemplate(id="report", action="synthesize_report", description="Synthesize final results", depends_on=["execute"]),
        ]
    )
)

WorkflowRegistry.register(
    WorkflowDefinition(
        type="research",
        steps=[
            WorkflowStepTemplate(id="research_plan", action="plan_subtasks", description="Plan deep research nodes", config={"strategy": "exhaustive"}),
            WorkflowStepTemplate(id="research_exec", action="execute_subtasks", description="Execute research gathering", depends_on=["research_plan"]),
            WorkflowStepTemplate(id="research_synth", action="synthesize_report", description="Synthesize research findings", depends_on=["research_exec"]),
        ]
    )
)

WorkflowRegistry.register(
    WorkflowDefinition(
        type="coding",
        steps=[
            WorkflowStepTemplate(id="coding_plan", action="plan_subtasks", description="Architect code changes"),
            WorkflowStepTemplate(id="coding_exec", action="execute_subtasks", description="Implement and test code", depends_on=["coding_plan"]),
            WorkflowStepTemplate(id="coding_synth", action="synthesize_report", description="Finalize implementation report", depends_on=["coding_exec"]),
        ]
    )
)

WorkflowRegistry.register(
    WorkflowDefinition(
        type="analysis",
        steps=[
            WorkflowStepTemplate(id="analysis_plan", action="plan_subtasks", description="Define analysis metrics"),
            WorkflowStepTemplate(id="analysis_exec", action="execute_subtasks", description="Process and analyze data", depends_on=["analysis_plan"]),
            WorkflowStepTemplate(id="analysis_synth", action="synthesize_report", description="Generate analytical summary", depends_on=["analysis_exec"]),
        ]
    )
)

WorkflowRegistry.register(
    WorkflowDefinition(
        type="smoke",
        steps=[
            WorkflowStepTemplate(id="prepare", action="prepare_digest", description="Prepare deterministic smoke payload"),
            WorkflowStepTemplate(id="validate", action="validate_payloads", description="Validate deterministic smoke payload", depends_on=["prepare"]),
            WorkflowStepTemplate(id="review", action="review_patch_bundle", description="Review deterministic smoke bundle", depends_on=["validate"]),
        ]
    )
)

WorkflowRegistry.register(
    WorkflowDefinition(
        type="system_modernization",
        steps=[
            WorkflowStepTemplate(id="audit_infrastructure", action="infra_audit", description="Scan system for legacy dependencies"),
            WorkflowStepTemplate(id="refactor_core", action="code_refactor", description="Apply architectural alignment patches", depends_on=["audit_infrastructure"]),
            WorkflowStepTemplate(id="verify_stability", action="health_check", description="Verify system integrity and performance", depends_on=["refactor_core"])
        ]
    )
)
WorkflowRegistry.register(
    WorkflowDefinition(
        type="self_repair",
        steps=[
            WorkflowStepTemplate(id="build_case", action="repair.build_case", description="Initialize repair incident context"),
            WorkflowStepTemplate(id="localize", action="repair.localize", description="Identify suspected files", depends_on=["build_case"]),
            WorkflowStepTemplate(id="plan", action="repair.plan", description="Generate multi-stage repair plan", depends_on=["localize"]),
            WorkflowStepTemplate(id="generate", action="repair.generate", description="Produce safe patch candidate", depends_on=["plan"]),
            WorkflowStepTemplate(id="sandbox", action="repair.sandbox", description="Verify patch in isolated environment", depends_on=["generate"]),
            WorkflowStepTemplate(id="verify", action="repair.verify", description="Run verifier mesh on candidate", depends_on=["sandbox"]),
            WorkflowStepTemplate(id="score", action="repair.score", description="Calculate risk and governance decision", depends_on=["verify"]),
            WorkflowStepTemplate(id="approval", action="taskflow.evaluate_gate", description="Human gate for high-risk changes", depends_on=["score"], condition="risk_score > 0.3"),
            WorkflowStepTemplate(id="rollout", action="repair.prepare_pr", description="Prepare PR for low-risk changes", depends_on=["score"], condition="risk_score <= 0.3"),
            WorkflowStepTemplate(id="learn", action="repair.learn", description="Update learning memory", depends_on=["rollout", "approval"]),
        ]
    )
)
