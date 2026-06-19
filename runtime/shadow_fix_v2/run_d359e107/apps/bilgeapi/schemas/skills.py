from typing import List, Optional
from pydantic import BaseModel, Field

class SkillMetadataResponse(BaseModel):
    name: str = Field(..., description="Unique name of the skill")
    source: str = Field(..., description="Source of the skill, e.g. external-vendor or bilgeapi-custom")
    version: str = Field(..., description="Version of the skill")
    license: str = Field("MIT", description="License of the skill")
    risk_level: str = Field("low", description="Risk level, e.g. low, medium, high_value_policy")
    allowed_use: List[str] = Field(default_factory=list, description="Allowed use cases")
    forbidden_use: List[str] = Field(default_factory=list, description="Forbidden use cases")
    hash: str = Field(..., description="SHA-256 hash of the skill markdown file")
    enabled: bool = Field(True, description="Whether the skill is enabled")
    description: Optional[str] = Field(None, description="Detailed description parsed from the markdown file")
    category: Optional[str] = Field(None, description="Category of the skill, e.g. Define, Plan, Build, Verify, Review, Ship")

class SkillCheckRequest(BaseModel):
    target_type: str = Field(..., description="Type of target, e.g. improvement_proposal, self_healing_run")
    target_id: str = Field(..., description="ID of the target entity")
    skills: List[str] = Field(..., description="List of skill names to verify against")

class SkillCheckItem(BaseModel):
    skill: str = Field(..., description="Name of the skill checked")
    result: str = Field(..., description="Result status, e.g. passed, failed, blocked")
    reason: Optional[str] = Field(None, description="Reason for the check outcome")

class SkillCheckResponse(BaseModel):
    target_type: str = Field(..., description="Type of target checked")
    target_id: str = Field(..., description="ID of target checked")
    status: str = Field(..., description="Aggregated status: PASS, REVIEW_REQUIRED, BLOCKED")
    passed: bool = Field(..., description="True if status is PASS")
    checks: List[SkillCheckItem] = Field(default_factory=list, description="Detailed check outcome list")
