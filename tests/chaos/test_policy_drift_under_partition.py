import pytest
import asyncio
import os
import yaml
from services.governance.policy_sync import PolicySync

@pytest.mark.asyncio
async def test_policy_drift_detection():
    """
    Scenario:
    - Region is isolated and a local configuration change happens (Drift).
    - Upon reconciliation, the mesh must detect the divergence from the GitOps baseline.
    """
    sync = PolicySync(primary_config_dir="configs/")
    
    # 1. Capture original checksums (Baseline)
    baseline_checksums = sync.get_local_checksums()
    policy_file = "emergency_policy.yaml"
    policy_path = os.path.join("configs/", policy_file)

    # Ensure policy file exists
    if not os.path.exists(policy_path):
        with open(policy_path, "w") as f:
            yaml.dump({"version": "1.0", "mode": "SAFE"}, f)
        baseline_checksums = sync.get_local_checksums()

    # 2. Simulate Drift (Manual local edit)
    with open(policy_path, "a") as f:
        f.write("\n# UNAUTHORIZED_DRIFT_COMMENT")

    # 3. Verify Detection
    drifts = await sync.check_drift("us-east-1", baseline_checksums)
    
    assert len(drifts) > 0
    assert policy_file in drifts[0]
    print(f"\n[SUCCESS] Drift detected: {drifts[0]}")

    # Cleanup drift
    with open(policy_path, "r") as f:
        lines = f.readlines()
    with open(policy_path, "w") as f:
        f.writelines([l for l in lines if "# UNAUTHORIZED_DRIFT_COMMENT" not in l])

if __name__ == "__main__":
    asyncio.run(test_policy_drift_detection())
