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
    incident_type: str = "general_incident"
    target_component: str = "unknown_subsystem"
    payload: Dict[str, Any] = Field(default_factory=dict, alias="initial_state_payload")
    expected_outcome: str = "REPAIR_SUCCESS"
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
        """Lists available scenario IDs, searching recursively for .yaml/.json files."""
        scenarios = []
        for root, _, files in os.walk(self.base_path):
            for f in files:
                if f.endswith(".yaml") or f.endswith(".json"):
                    # For directories like re-001/case.yaml, use directory name as ID
                    if f in ["case.yaml", "scenario.json"]:
                        scenarios.append(os.path.basename(root))
                    else:
                        scenarios.append(f.split('.')[0])
        return sorted(list(set(scenarios)))

    def load_scenario(self, scenario_id: str) -> Optional[RepairScenario]:
        """Loads a specific scenario by ID, supporting recursive lookup."""
        target_file = None
        for root, _, files in os.walk(self.base_path):
            # Check for direct file naming
            if f"{scenario_id}.yaml" in files:
                target_file = os.path.join(root, f"{scenario_id}.yaml")
                break
            if f"{scenario_id}.json" in files:
                target_file = os.path.join(root, f"{scenario_id}.json")
                break
            
            # Check for directory-based naming (re-001/case.yaml)
            if os.path.basename(root) == scenario_id:
                if "case.yaml" in files:
                    target_file = os.path.join(root, "case.yaml")
                    break
                if "scenario.json" in files:
                    target_file = os.path.join(root, "scenario.json")
                    break

        if not target_file:
            logger.error(f"Scenario file not found for ID: {scenario_id}")
            return None
            
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                if target_file.endswith(".json"):
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
                
                # Adapting Legacy Schema (re-001 etc.)
                if "incident_id" in data and "id" not in data:
                    data["id"] = data["incident_id"]
                if "module" in data and "target_component" not in data:
                    data["target_component"] = data["module"]
                if "subsystem" in data and "target_component" not in data:
                    data["target_component"] = data["subsystem"]
                if "initial_state_payload" not in data:
                    data["initial_state_payload"] = data.get("payload", {})
                if "incident_type" not in data:
                    data["incident_type"] = data.get("type", "legacy_system_repair")
                if "title" not in data and "name" in data:
                     data["title"] = data["name"]
                
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
