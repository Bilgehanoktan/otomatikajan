import os
import sys
import argparse
from harness_utils import get_repo_root

def generate_plan_skeleton(goal: str, skills: list):
    root = get_repo_root()
    plan_path = os.path.join(root, "implementation_plan.md")
    
    # Mevcut plan varsa yedekle
    if os.path.exists(plan_path):
        os.rename(plan_path, plan_path + ".bak")
        
    plan_content = f"""# Implementation Plan: {goal}

## User Review Required
> [!IMPORTANT]
> Bu plan Codex Harness tarafından otomatik taslak olarak oluşturulmuştur.

## Proposed Changes

### ECC Skills Integrated
"""
    for skill in skills:
        plan_content += f"- [ ] `{skill}` (Aktif skill bağlamı)\n"
        
    plan_content += """
## Verification Plan
- [ ] scripts/harness/doctor ile sistem sağlığını doğrula
- [ ] Manuel testler
"""
    
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(plan_content)
    
    print(f"[OK] Plan taslağı oluşturuldu: {plan_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("goal", help="Hedef açıklama")
    parser.add_argument("--skills", nargs="+", help="Kullanılacak skiller", default=[])
    args = parser.parse_args()
    
    generate_plan_skeleton(args.goal, args.skills)
