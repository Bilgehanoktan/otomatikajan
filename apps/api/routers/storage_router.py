from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import os
import uuid
import shutil
from apps.api.routers.apps.api.routers.auth.jwt_auth import get_current_user
from packages.observability.logging import get_logger

logger = get_logger("api.storage")
router = APIRouter(prefix="/storage", tags=["Sistem Depolama"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    """Dosya yükleme noktası. Yüklenen dosyanın URL'sini döner."""
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".txt", ".log"]:
            raise HTTPException(status_code=400, detail="Desteklenmeyen dosya formatı")

        file_id = str(uuid.uuid4().hex[:12])
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_url = f"/uploads/{filename}"
        logger.info(f"Dosya yüklendi: {filename} (Yükleyen: {current_user.email})")
        
        return {
            "url": file_url,
            "filename": filename,
            "size": os.path.getsize(file_path),
            "type": file.content_type
        }
    except Exception as e:
        logger.error(f"Yükleme hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Dosya kaydedilemedi: {str(e)}")
