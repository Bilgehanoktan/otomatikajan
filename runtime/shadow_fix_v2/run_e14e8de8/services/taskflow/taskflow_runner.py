from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.taskflow.taskflow_engine import run_workflow
from services.taskflow.taskflow_models import to_plain_data
from services.taskflow.taskflow_registry import list_workflows, workflow_exists


def _load_json_payload(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _main() -> int:
    parser = argparse.ArgumentParser(description="Run Egemen YAZ TaskFlow workflow.")
    parser.add_argument("--workflow", required=True, help="Workflow name or YAML path.")
    parser.add_argument("--input", required=True, help="Path to failed test or trace payload JSON.")
    parser.add_argument("--output-root", default=None, help="Optional output root. Defaults to repair_outputs/.")
    args = parser.parse_args()

    if not workflow_exists(args.workflow):
        available = ", ".join(list_workflows()) or "none"
        raise SystemExit(f"Workflow bulunamadi: {args.workflow}. Mevcut workflow'lar: {available}")

    run = run_workflow(args.workflow, _load_json_payload(args.input), output_root=args.output_root)
    print(json.dumps(to_plain_data(run), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
