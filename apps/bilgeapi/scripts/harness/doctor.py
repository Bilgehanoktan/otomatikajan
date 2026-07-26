import os
import sys
from harness_utils import check_dir, check_file, get_repo_root

def run_doctor():
    root = get_repo_root()
    sys.path.append(root) # Root'u ekle ki services/agents paketleri bulunsun
    print(f"--- Codex Harness Doctor - Root: {root} ---\n")
    
    issues = 0
    
    # 1. Klasör Yapısı
    if not check_dir(os.path.join(root, ".codex"), "Codex Config Dizini"): issues += 1
    if not check_dir(os.path.join(root, ".agents/skills"), "Skill Kataloğu"): issues += 1
    if not check_dir(os.path.join(root, "rules"), "Kurallar Dizini"): issues += 1
    
    # 2. Kritik Dosyalar
    if not check_file(os.path.join(root, ".codex/config.toml"), "Codex Config"): issues += 1
    if not check_file(os.path.join(root, "AGENTS.md"), "Ajan Talimatları"): issues += 1
    
    # 3. Skill Kontrolü
    from services.orchestration.application.skill_catalog import skill_catalog
    skills = skill_catalog.list_skills()
    print(f"STATUS: Aktif Skill Sayısı: {len(skills)}")
    if len(skills) == 0:
        print("WARNING: Hiçbir skill yüklü değil veya keşfedilemedi.")
        issues += 1
    else:
        for skill in skills[:5]: # İlk 5 tanesini göster
            print(f"  - [OK] {skill.skill_id}: {skill.name}")
        if len(skills) > 5: print(f"    ... ve {len(skills)-5} daha.")

    # 4. Prompt Manager & Governance Kontrolü
    try:
        sys.path.append(root)
        from services.orchestration.application.prompt_manager import prompt_manager
        if prompt_manager._governance_contract:
            print(f"[OK] Governance kontratı aktif ({len(prompt_manager._governance_contract)} karakter).")
        else:
            print("[WARNING] Governance kontratı boş!")
            issues += 1
    except Exception as e:
        print(f"[FAIL] PromptManager entegrasyon HATASI: {e}")
        issues += 1
        
    print(f"\n--- Doctor taraması bitti. Toplam sorun: {issues} ---")
    if issues == 0:
        print("RESULT: Sistem SAĞLIKLI.")
    else:
        print("RESULT: Bazı düzeltmeler gerekiyor.")

if __name__ == "__main__":
    run_doctor()
