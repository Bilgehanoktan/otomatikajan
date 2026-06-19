from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from services.project_factory.models import TaskItem, ProjectFactoryIntake
from services.project_factory.artifacts import _resolve_project_dir

def generate_task_breakdown(
    brief: ProjectFactoryIntake,
    template_name: str,
    allowed_outputs: List[str],
    workspace_root: Optional[str] = None
) -> List[TaskItem]:
    """
    Analyzes the project brief and scaffold manifest to produce a list of tasks.
    Writes the resulting breakdown to task_breakdown.json.
    """
    tasks = []
    
    # 1. Analyze and Plan Step
    tasks.append(TaskItem(
        task_id="TASK-PLAN",
        description=f"Analyze project brief for '{brief.title}' and map architectural requirements.",
        status="PENDING",
        estimated_minutes=10
    ))
    
    # 2. Template Scaffolding Step
    tasks.append(TaskItem(
        task_id="TASK-SCAFFOLD",
        description=f"Scaffold project boilerplates using template '{template_name}'.",
        status="PENDING",
        estimated_minutes=5
    ))
    
    # 3. Create Deliverables Steps
    for idx, outfile in enumerate(allowed_outputs):
        tasks.append(TaskItem(
            task_id=f"TASK-GEN-{idx + 1}",
            description=f"Generate and populate sandbox deliverable: '{outfile}' containing required logic.",
            status="PENDING",
            estimated_minutes=15
        ))
        
    # 4. Verification Step
    tasks.append(TaskItem(
        task_id="TASK-VERIFY",
        description="Execute sandbox-safe verification checks, unit-tests, and code linting.",
        status="PENDING",
        estimated_minutes=10
    ))
    
    # 5. Packaging Step
    tasks.append(TaskItem(
        task_id="TASK-PACKAGE",
        description="Compile verification metadata, checklist validation, and package implementation candidate.",
        status="PENDING",
        estimated_minutes=5
    ))

    # Write to task_breakdown.json
    project_dir = _resolve_project_dir(brief.project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)
    
    breakdown_path = project_dir / "task_breakdown.json"
    with open(breakdown_path, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in tasks], f, indent=2, ensure_ascii=False)
        
    return tasks

def load_task_breakdown(
    project_id: str,
    workspace_root: Optional[str] = None
) -> List[TaskItem]:
    """
    Loads task_breakdown.json.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    breakdown_path = project_dir / "task_breakdown.json"
    if not breakdown_path.exists():
        return []
        
    with open(breakdown_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [TaskItem(**item) for item in data]

def update_task_status(
    project_id: str,
    task_id: str,
    status: str,
    workspace_root: Optional[str] = None
) -> None:
    """
    Updates the status of a specific task item in task_breakdown.json.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    breakdown_path = project_dir / "task_breakdown.json"
    if not breakdown_path.exists():
        return
        
    tasks = load_task_breakdown(project_id, workspace_root)
    for task in tasks:
        if task.task_id == task_id:
            task.status = status
            break
            
    with open(breakdown_path, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in tasks], f, indent=2, ensure_ascii=False)
