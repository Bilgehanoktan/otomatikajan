from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional, Any
import uuid
from auth.jwt_auth import get_current_user, require_admin

router = APIRouter(prefix="/self-update", tags=["Self-Update"])

# ─── Şemalar ──────────────────────────────────────────────
class SelfUpdateHistoryItem(BaseModel):
    date: str
    target_file: str
    description: str
    rationale: str
    backup_path: Optional[str] = None
    status: str
    version_before: str
    version_after: str
    diff_summary: Optional[str] = None
    changed_symbols: List[str] = []
    test_result: dict = {}
    git_commit: Optional[str] = None

class SelfUpdateState(BaseModel):
    current_version: str
    last_updated: str
    updates: List[SelfUpdateHistoryItem]

class SelfUpdateRequest(BaseModel):
    target_file_path: str
    instruction: str
    async_mode: bool = True

class SelfUpdateResponse(BaseModel):
    message: str
    job_id: Optional[str] = None

# ─── Dependency ───────────────────────────────────────────
def _orch():
    from core.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
    return orchestrator

def _queue():
    from core.job_queue import job_queue
    return job_queue

# ─── Endpoint'ler ─────────────────────────────────────────

@router.get("/state")
async def get_system_state(current_user=Depends(get_current_user)):
    """Sistemin mevcut sürüm ve güncelleme geçmişini döner."""
    orch = _orch()
    if not orch.self_updater:
        raise HTTPException(status_code=503, detail="Self-Updater aktif degil.")
    return orch.self_updater.registry.get_state()

@router.post("/apply", response_model=SelfUpdateResponse)
async def apply_self_modification(request_data: SelfUpdateRequest, current_user=Depends(require_admin)):
    """
    Sistemin kendi kodunu değiştirmesini tetikler.
    async_mode=True: Job Queue üzerinden çalışır.
    async_mode=False: Bloklayarak bekler (test için).
    """
    orch = _orch()
    queue = _queue()
    
    if not orch.self_updater:
        raise HTTPException(status_code=503, detail="Self-Updater aktif degil.")

    if request_data.async_mode:
        job = await queue.enqueue(
            "self_update",
            target_file_path=request_data.target_file_path,
            instruction=request_data.instruction
        )
        return SelfUpdateResponse(
            message="Self-update işi kuyruğa alındı.",
            job_id=job.id
        )
    else:
        result = await orch.self_updater.modify_system_file(
            target_file_path=request_data.target_file_path,
            instruction=request_data.instruction
        )
        if "Başarısız" in result:
            raise HTTPException(status_code=400, detail=result)
        return SelfUpdateResponse(message=result)

@router.get("/index/search")
async def search_codebase(query: str, limit: int = 5, current_user=Depends(get_current_user)):
    """Kod indeksi üzerinde semantik/kelime araması yapar."""
    orch = _orch()
    if not orch.self_updater:
        raise HTTPException(status_code=503, detail="Self-Updater aktif degil.")
    return orch.self_updater.indexer.search(query=query, limit=limit)

@router.post("/index/rebuild")
async def rebuild_index(current_user=Depends(require_admin)):
    """Kod indeksini manuel olarak tazeler."""
    orch = _orch()
    if not orch.self_updater:
        raise HTTPException(status_code=503, detail="Self-Updater aktif degil.")
    orch.self_updater.indexer.build_index()
    return {"status": "rebuilding"}
