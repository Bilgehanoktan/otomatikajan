"""
libs/workflow/registry.py — Phase 13.04
Central registry for workflow types and their required execution steps.
"""
from typing import Dict, List, Type, Any
from pydantic import BaseModel

class WorkflowStepTemplate(BaseModel):
    id: str
    action: str
    description: str
    depends_on: List[str] = []
    config: Dict[str, Any] = {}

class WorkflowDefinition(BaseModel):
    type: str # e.g., "feature_dev", "bug_fix", "refactor"
    steps: List[WorkflowStepTemplate]

class WorkflowRegistry:
    """Registry that maps workflow types to their step sequences."""
    
    _definitions: Dict[str, WorkflowDefinition] = {}

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
        type="system_modernization",
        steps=[
            WorkflowStepTemplate(
                id="audit_infrastructure",
                action="infra_audit",
                description="Scan system for legacy dependencies"
            ),
            WorkflowStepTemplate(
                id="refactor_core",
                action="code_refactor",
                description="Apply architectural alignment patches",
                depends_on=["audit_infrastructure"]
            ),
            WorkflowStepTemplate(
                id="verify_stability",
                action="health_check",
                description="Verify system integrity and performance",
                depends_on=["refactor_core"]
            )
        ]
    )
)
