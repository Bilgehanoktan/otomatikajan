from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from packages.contracts.states import ArtifactType

class Artifact(BaseModel):
    name: str
    type: ArtifactType
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
