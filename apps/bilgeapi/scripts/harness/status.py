import os
import sys
from harness_utils import get_repo_root

def show_status():
    root = get_repo_root()
    print(f"--- Codex Harness Status - {root} ---\n")
    
    # Skills
    skills_dir = os.path.join(root, ".agents/skills")
    if os.path.exists(skills_dir):
        print("SKILLS:")
        for d in os.listdir(skills_dir):
            if os.path.isdir(os.path.join(skills_dir, d)):
                print(f"  - {d}")
    
    # Rules
    rules_dir = os.path.join(root, "rules")
    if os.path.exists(rules_dir):
        print("\nRULES:")
        rules = [f for f in os.listdir(rules_dir) if f.endswith(".md")]
        print(f"  {len(rules)} kural dosyası mevcut.")

    # Config Summary
    config_path = os.path.join(root, ".codex/config.toml")
    if os.path.exists(config_path):
        print("\nCONFIG:")
        with open(config_path, "r") as f:
            lines = f.readlines()
            for line in lines[:10]: # İlk 10 satır
                if "=" in line:
                    print(f"  {line.strip()}")

if __name__ == "__main__":
    show_status()
