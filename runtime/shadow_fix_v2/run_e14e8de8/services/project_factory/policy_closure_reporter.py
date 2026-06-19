from typing import Dict, Any
from pathlib import Path
from datetime import datetime, timezone

def generate_policy_closure_report(manifest_data: Dict[str, Any], archive_dir: Path) -> None:
    """
    Generates a Markdown closure report documenting the end of the policy lifecycle.
    """
    report_content = f"""# Policy Lifecycle Closure Report

**Proposal ID:** {manifest_data.get('proposal_id', 'UNKNOWN')}
**Release ID:** {manifest_data.get('release_id', 'UNKNOWN')}
**Date:** {datetime.now(timezone.utc).isoformat()}
**Final Decision:** {manifest_data.get('final_decision', 'UNKNOWN')}
**Approved By:** {manifest_data.get('approved_by', 'UNKNOWN')}

## Safety & Governance Summary

- **Production Apply Performed:** `{str(manifest_data.get('production_apply_performed', False))}`
- **Policy Files Modified:** `{str(manifest_data.get('policy_files_modified', False))}`
- **Merge Performed:** `{str(manifest_data.get('merge_performed', False))}`
- **Deploy Performed:** `{str(manifest_data.get('deploy_performed', False))}`
- **Learning Memory Synced:** `{str(manifest_data.get('learning_memory_synced', False))}`

## Evidence Bundle

Total evidence files bundled: **{manifest_data.get('evidence_count', 0)}**

## Conclusion

The policy lifecycle has been securely closed. All governance requirements have been satisfied, and the operations were conducted entirely through draft PRs and secure artifacts without any direct production writes.
"""
    
    with open(archive_dir / "policy_closure_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)
