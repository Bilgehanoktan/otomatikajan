import os
import re

versions_dir = 'e:/ai_company_faz12.1/libs/db/migrations/alembic/versions/'

# Map of old IDs to new shortened IDs
short_map = {
    '0010_add_operational_governance_tables': '0010_operational_gov',
    '0011_add_isolation_and_autonomy_fields': '0011_isolation_autonomy',
    '0013_add_evolution_lineage_tables': '0013_evolution_tables',
    '0014_sif_01_identity_and_permissions': '0014_sif01_identity',
    '0015_add_outcome_to_decision_lineage': '0015_outcome_lineage',
    '0016_add_fleet_orchestra_tables': '0016_fleet_orch',
    '0bee69d3bd29_add_resilience_fields_v2': '0bee69d3bd29_resilience_v2',
    '0d32eda31fe6_add_policy_evolution_tables': '0d32eda31fe6_policy_evol',
    '33bbc921964e_add_causal_and_inhibition_fields_to_': '33bbc921964e_causal_inhib',
    '4bd5655fe01b_add_governance_observability_tables': '4bd5655fe01b_gov_obs',
    '54a09b9b7ba4_add_meta_governor_tables': '54a09b9b7ba4_meta_gov',
    '61034897bc59_add_internal_monologue_to_subtasks': '61034897bc59_internal_mono',
    '7cc9f44bc8d0_add_phase_80_sovereign_goals_and_goal_id': '7cc9f44bc8d0_goals',
    'dfd787c12448_add_governor_resilience_tables': 'dfd787c12448_resilience',
    'e4a7b5d12345_add_governance_proof_fabric': 'e4a7b5d12345_proof_fabric',
    'f002a05eadd5_add_updated_at_to_projects_and_sync_': 'f002a05eadd5_update_sync',
    'af7ebd1309a2_standardize_status_and_project_id_sync': 'af7ebd1309a2_status_sync',
    'cce4d9bf9404_add_budget_limit_to_project_table': 'cce4d9bf9404_budget_limit'
}

for filename in os.listdir(versions_dir):
    if not filename.endswith('.py'):
        continue
    
    filepath = os.path.join(versions_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old_id, new_id in short_map.items():
        # Match revision: str = 'old_id' or revision = 'old_id' (single or double quotes)
        new_content = re.sub(f"(['\"]){old_id}(['\"])", f"\\g<1>{new_id}\\g<2>", new_content)
        # Also match the Revision ID: old_id in docstrings
        new_content = new_content.replace(f"Revision ID: {old_id}", f"Revision ID: {new_id}")
        new_content = new_content.replace(f"Revises: {old_id}", f"Revises: {new_id}")

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filename}")
