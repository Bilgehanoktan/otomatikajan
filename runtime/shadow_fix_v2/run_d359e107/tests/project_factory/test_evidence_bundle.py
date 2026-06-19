"""Tests for Evidence Bundle Builder."""
import pytest
from services.project_factory.evidence_bundle import build_evidence_bundle, REQUIRED_EVIDENCE_FILES


def test_build_evidence_bundle_all_present(tmp_path):
    """If all required files are present, all are copied."""
    project_dir = tmp_path / "project_outputs" / "project_factory" / "PF-1"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy files
    for filename in REQUIRED_EVIDENCE_FILES:
        (project_dir / filename).write_text("dummy")

    copied, missing = build_evidence_bundle("PF-1", str(tmp_path))
    
    assert len(copied) == len(REQUIRED_EVIDENCE_FILES)
    assert len(missing) == 0
    
    bundle_dir = project_dir / "release_archive" / "evidence_bundle"
    for filename in REQUIRED_EVIDENCE_FILES:
        assert (bundle_dir / filename).exists()


def test_build_evidence_bundle_some_missing(tmp_path):
    """Missing files are reported correctly."""
    project_dir = tmp_path / "project_outputs" / "project_factory" / "PF-1"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create only the first 3 files
    for filename in REQUIRED_EVIDENCE_FILES[:3]:
        (project_dir / filename).write_text("dummy")

    copied, missing = build_evidence_bundle("PF-1", str(tmp_path))
    
    assert len(copied) == 3
    assert len(missing) == len(REQUIRED_EVIDENCE_FILES) - 3
    assert REQUIRED_EVIDENCE_FILES[0] in copied
    assert REQUIRED_EVIDENCE_FILES[-1] in missing
