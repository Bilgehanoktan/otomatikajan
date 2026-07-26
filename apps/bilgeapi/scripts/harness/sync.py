import os
import shutil
import logging
from harness_utils import get_repo_root

def sync_skills():
    root = get_repo_root()
    legacy_dir = os.path.join(root, ".legacy_archive/external/agent_assets/skills")
    local_dir = os.path.join(root, ".agents/skills")
    
    print(f"--- Syncing Skills from Legacy Archive ---")
    
    if not os.path.exists(legacy_dir):
        print(f"[FAIL] Legacy archive bulunamadı: {legacy_dir}")
        return

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    synced = 0
    # Sadece belirli bir seti veya tümünü mü senkronize edelim? 
    # Şimdilik mevcut kataloğa göre yeni olanları ekleyelim.
    for item in os.listdir(legacy_dir):
        legacy_path = os.path.join(legacy_dir, item)
        local_path = os.path.join(local_dir, item)
        
        if os.path.isdir(legacy_path):
            if not os.path.exists(local_path):
                print(f"[SYNC] Yeni skill bulundu: {item}")
                shutil.copytree(legacy_path, local_path)
                synced += 1
        elif item.endswith(".md"): # Bazı skiller tek dosya olabilir
            skill_name = item.replace(".md", "")
            local_skill_dir = os.path.join(local_dir, skill_name)
            if not os.path.exists(local_skill_dir):
                print(f"[SYNC] Yeni skill (file-based) bulundu: {skill_name}")
                os.makedirs(local_skill_dir)
                shutil.copy(legacy_path, os.path.join(local_skill_dir, "SKILL.md"))
                synced += 1
                
    print(f"\n--- Sync bitti. {synced} yeni skill eklendi. ---")

if __name__ == "__main__":
    sync_skills()
