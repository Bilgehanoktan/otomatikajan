import os
import yaml
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger("repair_bench.loader")

class RepairScenario(BaseModel):
    """Scientific representation of an incident to be repaired."""
    scenario_id: str = Field(alias="id")
    name: str = Field(alias="title")
    incident_type: str
    target_component: str
    payload: Dict[str, Any] = Field(alias="initial_state_payload")
    expected_outcome: str = "RESOLVED"
    success_criteria: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True

class BenchmarkLoader:
    """Loads repair scenarios from the engineering benchmark pool."""
    
    def __init__(self, base_path: str = "benchmarks/repair_bench/cases"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

    def list_scenarios(self) -> List[str]:
        """Lists available scenario IDs."""
        return [f.split('.')[0] for f in os.listdir(self.base_path) if f.endswith(".yaml") or f.endswith(".json")]

    def load_scenario(self, scenario_id: str) -> Optional[RepairScenario]:
        """Loads a specific scenario by ID."""
        yaml_path = os.path.join(self.base_path, f"{scenario_id}.yaml")
        json_path = os.path.join(self.base_path, f"{scenario_id}.json")
        
        file_path = yaml_path if os.path.exists(yaml_path) else json_path
        if not os.path.exists(file_path):
            logger.error(f"Scenario file not found: {scenario_id}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith(".json"):
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
                return RepairScenario(**data)
        except Exception as e:
            logger.error(f"Failed to parse scenario {scenario_id}: {e}")
            return None

    def export_incident_to_scenario(self, incident_data: Dict[str, Any], scenario_id: str) -> str:
        """Converts a production incident into a reproducible benchmark scenario."""
        scenario = RepairScenario(
            id=scenario_id,
            title=f"Captured Incident: {incident_data.get('message', 'Unknown')[:50]}",
            incident_type=incident_data.get('incident_type', 'general'),
            target_component=incident_data.get('payload', {}).get('component', 'unknown'),
            initial_state_payload=incident_data.get('payload', {}),
            tags=["captured_from_prod"]
        )
        
        file_path = os.path.join(self.base_path, f"{scenario_id}.yaml")
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(scenario.dict(), f, sort_keys=False)
            
        return file_path

if __name__ == "__main__":
    # Quick sanity check
    loader = BenchmarkLoader()
    print(f"Loaded {len(loader.list_scenarios())} scenarios from {loader.base_path}")
