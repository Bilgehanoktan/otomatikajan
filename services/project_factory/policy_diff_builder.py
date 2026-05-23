from typing import Optional
from services.project_factory.models import PolicyApplyPreview
from services.project_factory.artifacts import write_policy_diff_summary

def build_policy_diff_summary(preview: PolicyApplyPreview, workspace_root: Optional[str] = None) -> None:
    lines = []
    lines.append("# Policy Apply Preview\n")
    lines.append(f"Production apply performed: {str(preview.production_apply_performed).lower()}")
    lines.append(f"Policy files modified: {str(preview.policy_files_modified).lower()}\n")
    
    lines.append("## Proposed Changes")
    if not preview.preview_changes:
        lines.append("None")
    else:
        for c in preview.preview_changes:
            lines.append(f"- {c.change_type} {c.target_file}")
            lines.append(f"  - Add {c.field}:")
            if c.add:
                for a in c.add:
                    lines.append(f"    - {a}")
            elif c.update:
                lines.append(f"    - Update: {c.update}")
                
    lines.append("\n## Blocking Risks")
    if not preview.blocking_risks:
        lines.append("None")
    else:
        for r in preview.blocking_risks:
            lines.append(f"- {r}")
            
    content = "\n".join(lines)
    write_policy_diff_summary(content, workspace_root, preview.proposal_id)
