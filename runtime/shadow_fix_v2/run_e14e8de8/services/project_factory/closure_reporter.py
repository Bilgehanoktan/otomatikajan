"""
Closure Report Generator.

Produces a human-readable closure_report.md summarizing the entire
project lifecycle from intake to final decision.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from services.project_factory.artifacts import _resolve_project_dir, _load_json_artifact


def generate_closure_report(
    project_id: str,
    operator_id: str,
    rationale: str,
    release_id: str,
    copied_evidence: List[str],
    missing_evidence: List[str],
    workspace_root: Optional[str] = None,
) -> str:
    """
    Generates closure_report.md inside release_archive/.
    Returns the report content.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    archive_dir = project_dir / "release_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Load key artifacts for summary
    brief = _load_json_artifact(project_id, "project_brief.json", workspace_root)
    pr_review = _load_json_artifact(project_id, "pr_review_report.json", workspace_root)
    pr_creation = _load_json_artifact(project_id, "draft_pr_creation.json", workspace_root)
    delivery = _load_json_artifact(project_id, "delivery_manifest.json", workspace_root)

    title = brief.get("title", project_id) if brief else project_id
    pr_url = ""
    fallback_note = ""
    if pr_creation and pr_creation.get("pr_url"):
        pr_url = pr_creation["pr_url"]
    else:
        fallback_note = (
            "\n> [!NOTE]\n"
            "> Draft PR creation was not available; release archive is evidence-only.\n"
        )

    review_status = pr_review.get("status", "UNKNOWN") if pr_review else "UNKNOWN"
    risk_score = pr_review.get("risk_score", "N/A") if pr_review else "N/A"
    quality_score = pr_review.get("quality_score", "N/A") if pr_review else "N/A"

    now = datetime.now(timezone.utc).isoformat()

    report = f"""# Closure Report — {release_id}

## Project Summary
- **Project ID:** {project_id}
- **Title:** {title}
- **Release ID:** {release_id}
- **Final Decision:** FINAL_APPROVED
- **Approved By:** {operator_id}
- **Closed At:** {now}

## Operator Rationale
{rationale}
{fallback_note}
## Safety Confirmation

| Check | Status |
|-------|--------|
| production_apply_performed | ❌ false |
| merge_performed | ❌ false |
| deploy_performed | ❌ false |

## Review Summary
- **PR Review Status:** {review_status}
- **Risk Score:** {risk_score}
- **Quality Score:** {quality_score}
- **PR URL:** {pr_url if pr_url else "N/A (local candidate)"}

## Evidence Bundle
**Collected:** {len(copied_evidence)} artifact(s)
**Missing:** {len(missing_evidence)} artifact(s)

### Collected Evidence
"""

    for f in copied_evidence:
        report += f"- ✅ `{f}`\n"

    if missing_evidence:
        report += "\n### Missing Evidence\n"
        for f in missing_evidence:
            report += f"- ⚠️ `{f}`\n"

    report += """
---

> [!IMPORTANT]
> This release archive is **finalized and locked**. No production apply, merge, or deploy was performed.
> All evidence is preserved for audit and compliance purposes.
"""

    report_path = archive_dir / "closure_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    return report
