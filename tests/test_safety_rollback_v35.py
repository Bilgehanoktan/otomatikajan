import pytest
import os
import asyncio
from core.agi.security.backup_service import backup_service
from core.agi.cognitive.sovereign_cortex import SovereignCortex
from core.task_management import ProjectTask, SubTask, TaskStatus
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_shadow_backup_creation():
    """
    Kritik bir dosya (örneğin config.py simülasyonu) yazılmadan önce 
    yedeklendiğini doğrular.
    """
    test_file = "test_target_v35.txt"
    with open(test_file, "w") as f: f.write("original content")
    
    try:
        # 1. BackupService'in çalıştığını doğrula
        backup_id = backup_service.create_backup(test_file)
        assert os.path.exists(backup_id)
        print(f"Shadow Backup Created: {backup_id}")
        
        # 2. Geri yükleme testi
        with open(test_file, "w") as f: f.write("modified content")
        success = backup_service.restore_backup(test_file, backup_id)
        assert success
        
        with open(test_file, "r") as f:
            content = f.read()
            assert content == "original content"
        print("Recovery (Rollback): SUCCESS")
        
    finally:
        if os.path.exists(test_file): os.remove(test_file)
        # Backup dosyaları .backup/ altında kalır (manual cleanup test edilebilir)

@pytest.mark.asyncio
async def test_sovereign_pre_execution_backup_trigger():
    """
    SovereignCortex'in bir 'writer' ajanı çalıştırırken 
    dosya ismini prompt'tan yakalayıp yedekleme yaptığını doğrular.
    """
    cortex = SovereignCortex()
    test_file = "to_be_backed_up.py"
    with open(test_file, "w") as f: f.write("code v1")
    
    task = ProjectTask(id="test_t_35", title="Safety Test")
    subtask = SubTask(
        id="st_35", 
        agent_id="backend_dev", 
        prompt=f"Please update {test_file} to v2.",
        status=TaskStatus.PENDING
    )
    
    # Velocity engine'i mock'la (Yürütmeyi simüle et ama asıl yazmayı yapmasın)
    with patch("core.agi.operational.velocity_engine.velocity_engine.simulate_and_execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = MagicMock(success=True)
        
        # 1. Yürütme
        await cortex._execute_subtask_nexus(subtask, task)
        
        # 2. Doğrulama: .backup/ dizininde dosya ismimizi içeren bir .bak olmalı
        backup_found = False
        for root, _, files in os.walk(".backup"):
            for f in files:
                if "to_be_backed_up.py" in f:
                    backup_found = True
                    break
        
        assert backup_found
        print("Sovereign Pre-Execution Trigger: SUCCESS")
        
    if os.path.exists(test_file): os.remove(test_file)

if __name__ == "__main__":
    asyncio.run(test_shadow_backup_creation())
    asyncio.run(test_sovereign_pre_execution_backup_trigger())
