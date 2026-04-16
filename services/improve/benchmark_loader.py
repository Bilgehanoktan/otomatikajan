
import os
import yaml
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.observability.logging import get_logger

logger = get_logger("repair.bench_loader")

class BenchmarkCase(BaseModel):
    id: str
    incident_id: str
    module: str
    title: str
    description: str
    risk_class: str
    cost_class: str
    target_behavior: str
    verification_profile: Dict[str, Any]
    input_context: Dict[str, Any]
    expected_signals: Dict[str, Any]

class RepairBenchLoader:
    def __init__(self, base_path: str = "benchmarks/repair_bench"):
        self.base_path = base_path
        self.cases_dir = os.path.join(base_path, "cases")

    def load_index(self) -> List[Dict[str, Any]]:
        index_path = os.path.join(self.base_path, "index.yaml")
        if not os.path.exists(index_path):
            logger.warning(f"Index not found at {index_path}")
            return []
        with open(index_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("cases", [])

    def load_case(self, case_id: str) -> Optional[BenchmarkCase]:
        case_path = os.path.join(self.cases_dir, case_id)
        case_yaml = os.path.join(case_path, "case.yaml")
        context_json = os.path.join(case_path, "input_context.json")
        signals_json = os.path.join(case_path, "expected_signals.json")

        if not os.path.exists(case_yaml):
            logger.error(f"Case YAML not found for {case_id}")
            return None

        try:
            with open(case_yaml, "r", encoding="utf-8") as f:
                case_data = yaml.safe_load(f)
            
            with open(context_json, "r", encoding="utf-8") as f:
                context_data = json.load(f)
                
            with open(signals_json, "r", encoding="utf-8") as f:
                signals_data = json.load(f)

            return BenchmarkCase(
                id=case_id,
                incident_id=case_data.get("incident_id", ""),
                module=case_data.get("module", ""),
                title=case_data.get("title", ""),
                description=case_data.get("description", ""),
                risk_class=case_data.get("risk_class", "medium"),
                cost_class=case_data.get("cost_class", "low"),
                target_behavior=case_data.get("target_behavior", ""),
                verification_profile=case_data.get("verification_profile", {}),
                input_context=context_data,
                expected_signals=signals_data
            )
        except Exception as e:
            logger.error(f"Failed to load case {case_id}: {e}")
            return None

    def list_all_cases(self) -> List[BenchmarkCase]:
        index = self.load_index()
        cases = []
        for entry in index:
            case = self.load_case(entry["id"])
            if case:
                cases.append(case)
        return cases
