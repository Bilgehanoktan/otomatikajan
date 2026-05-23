from typing import Optional, Dict, Any
from pathlib import Path

from services.project_factory.artifacts import _resolve_policy_autopilot_dir, write_policy_release_manifest, write_policy_learning_memory_sync
from services.project_factory.models import PolicyReleaseManifest
from services.project_factory.policy_evidence_bundle import build_policy_evidence_bundle
from services.project_factory.policy_learning_memory_sync import build_policy_learning_memory_sync
from services.project_factory.policy_closure_reporter import generate_policy_closure_report

def create_policy_release_archive(proposal_id: str, operator_id: str, final_decision: str, workspace_root: Optional[str] = None) -> PolicyReleaseManifest:
    """
    Orchestrates the creation of the final release archive.
    """
    source_dir = _resolve_policy_autopilot_dir(workspace_root, proposal_id)
    archive_dir = source_dir / "policy_release_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    release_id = f"PREL-{proposal_id}"
    
    # 1. Build learning memory sync artifact
    learning_sync = build_policy_learning_memory_sync(proposal_id, workspace_root)
    write_policy_learning_memory_sync(learning_sync.model_dump(), archive_dir)
    legacy_archive_dir = _resolve_policy_autopilot_dir(workspace_root) / "policy_release_archive"
    legacy_archive_dir.mkdir(parents=True, exist_ok=True)
    write_policy_learning_memory_sync(learning_sync.model_dump(), legacy_archive_dir)
    
    # 2. Build evidence bundle
    evidence_count = build_policy_evidence_bundle(archive_dir, workspace_root, proposal_id)
    legacy_evidence_count = build_policy_evidence_bundle(legacy_archive_dir, workspace_root)
    evidence_count = max(evidence_count, legacy_evidence_count)
    
    # 3. Build manifest
    manifest = PolicyReleaseManifest(
        proposal_id=proposal_id,
        release_id=release_id,
        status="POLICY_RELEASE_ARCHIVE_READY",
        final_decision=final_decision,
        approved_by=operator_id,
        production_apply_performed=False,
        policy_files_modified=False,
        merge_performed=False,
        deploy_performed=False,
        learning_memory_synced=True,
        evidence_count=evidence_count
    )
    
    manifest_dict = manifest.model_dump()
    write_policy_release_manifest(manifest_dict, archive_dir)
    write_policy_release_manifest(manifest_dict, legacy_archive_dir)
    
    # 4. Generate closure report
    generate_policy_closure_report(manifest_dict, archive_dir)
    generate_policy_closure_report(manifest_dict, legacy_archive_dir)
    
    return manifest
