import sys
import os
import uuid
import asyncio
from typing import Optional
from observability.logging import get_logger

# Proje köke python path ekle
sys.path.append(os.getcwd())

_log = get_logger("agi_self_patcher")

async def apply_evolution_patch(suggestion_id: str):
    """
    Onaylanan bir öz-evrim yamasını (CEOSuggestedTask) fiziksel dosyaya uygular.
    """
    from db.session import session_scope
    from db.models import CEOSuggestedTask
    from sqlalchemy import select
    
    print(f"--- AGI Self-Evolution Patcher ({suggestion_id}) ---")
    
    async with session_scope() as db:
        result = await db.execute(
            select(CEOSuggestedTask).where(CEOSuggestedTask.id == uuid.UUID(suggestion_id))
        )
        suggestion = result.scalar_one_or_none()
        
        if not suggestion:
            print(f"[ERROR] Suggestion {suggestion_id} not found.")
            return

        # 1. Dosya ve Yama Ayrıştırma
        # Description format: "File: <path>\n\nREASON: ...\n\nSUGGESTED PATCH:\n<patch>"
        desc = suggestion.description
        try:
            file_line = desc.split("\n")[0]
            target_file = file_line.replace("File: ", "").strip()
            
            patch_marker = "SUGGESTED PATCH:\n"
            if patch_marker not in desc:
                print("[ERROR] No patch found in suggestion description.")
                return
                
            new_code_block = desc.split(patch_marker)[1].strip()
            # Markdown block temizliği
            if new_code_block.startswith("```"):
                new_code_block = "\n".join(new_code_block.split("\n")[1:-1])
        except Exception as e:
            print(f"[ERROR] Failed to parse patch: {e}")
            return

        print(f"[INFO] Target File: {target_file}")
        
        # 2. Güvenlik Kontrolü (Dizin Sınırlaması)
        ALLOWED_PREFIXES = ["core/agi/", "scripts/", "tasks/"]
        if not any(target_file.startswith(p) for p in ALLOWED_PREFIXES):
            print(f"[CRITICAL] Blocked write attempt to unauthorized file: {target_file}")
            return

        # 3. Yedekleme (Optional Git Checkpoint)
        # os.system("git stash save 'AGI Evolution Pre-Patch'")

        # 4. Yamayı Oluştur (Evrimsel Mimar - Evolutionary Architect stratejisi)
        # Evolutionary Architect şu an tüm dosyayı değil, spesifik bir fonksiyonu döndürüyor olabilir.
        # Bu yüzden şimdilik 'Manual Review Required' uyarısı yapıp kullanıcı onayına bırakıyoruz.
        
        print("\nPROPOSED CHANGE:")
        print("-" * 30)
        print(new_code_block)
        print("-" * 30)
        
        confirm = input("\nBu yamayı uygulamak istiyor musunuz? (y/n): ")
        if confirm.lower() == 'y':
            try:
                # Gerçek uygulama (Bu aşama çok tehlikelidir, sadece test amaçlı limitli kullanım)
                # target_file'ı açıp yama yerini bulup değiştirmek gerçek diff tool gerektirir.
                # Şimdilik simüle ediyoruz veya tüm dosyayı güncelliyoruz.
                print(f"[OK] Yama '{target_file}' dosyasına başarıyla uygulandı (Simulated).")
                suggestion.status = "approved"
                await db.commit()
            except Exception as e:
                print(f"[ERROR] Patch application failed: {e}")
        else:
            print("[INFO] İşlem iptal edildi.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/apply_self_evolution.py <suggestion_id>")
        sys.exit(1)
    
    asyncio.run(apply_evolution_patch(sys.argv[1]))
