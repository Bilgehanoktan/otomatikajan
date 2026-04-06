from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, File, Form, HTTPException, UploadFile  # type: ignore
from fastapi.responses import StreamingResponse, FileResponse  # type: ignore
from prometheus_client import Counter, Summary, generate_latest, CONTENT_TYPE_LATEST  # type: ignore

from deerflow.client import DeerFlowClient  # type: ignore
from deerflow.config.paths import get_paths  # type: ignore
from packages.observability.logging import get_logger, configure_logging

logger = get_logger("deerflow_bridge", force_db=True)

app = FastAPI(title="DeerFlow Bridge")

# Prometheus Metrics
RELEASING = os.getenv("APP_ENV") == "production"
# ... existing metrics ...
REQUEST_COUNT = Counter("deerflow_requests_total", "Total DeerFlow requests", ["method", "endpoint"])
REQUEST_LATENCY = Summary("deerflow_request_latency_seconds", "Latency of DeerFlow requests", ["endpoint"])
ERROR_COUNT = Counter("deerflow_errors_total", "Total DeerFlow errors", ["type"])
TOKEN_COUNT = Counter("deerflow_tokens_total", "Total tokens used", ["type"])

# Singleton Client
CLIENT = DeerFlowClient(
    config_path=os.getenv("DEER_FLOW_CONFIG_PATH"),
    thinking_enabled=True,
    subagent_enabled=True,
    plan_mode=True,
)


@app.on_event("startup")
async def startup_event():
    configure_logging()
    logger.info("DeerFlow Bridge starting up...")
    from deerflow.config.paths import get_paths  # type: ignore
    paths = get_paths()
    base_dir = paths.base_dir
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        # Test write
        test_file = base_dir / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        logger.info(f"DeerFlow base_dir is writable: {base_dir}")
    except Exception as e:
        logger.error(f"DeerFlow base_dir is NOT writable ({base_dir}): {e}", exc_info=True)


@app.get("/")
async def root():
    return {
        "name": "DeerFlow Bridge",
        "status": "ready",
        "health_check": "/health",
        "metrics": "/metrics"
    }


@app.get("/health")
async def health():
    return {"ok": True, "status": "active"}


@app.get("/ping")
async def ping():
    """Ultra-fast reachability check."""
    return "pong"


@app.get("/ready")
async def readiness():
    """Full startup kontrolü tamamlanmış mı?"""
    return {"ready": True, "bridge": "deerflow", "version": "1.1.0"}


@app.get("/version")
async def version():
    """Bridge sürüm bilgisi."""
    return {"version": "1.1.0", "engine": "deer-flow", "api": "bridge/v1"}


@app.get("/capabilities")
async def capabilities():
    """Bridge'in desteklediği yetenekleri bildirir."""
    return {
        "streaming": True,
        "file_upload": True,
        "artifacts": True,
        "cancel": False,
        "plan_mode": True,
        "thinking": True,
        "subagent": True,
        "roles": ["planner", "researcher", "reviewer", "recovery"],
    }


@app.get("/metrics")
async def metrics():
    return StreamingResponse(iter([generate_latest()]), media_type=CONTENT_TYPE_LATEST)


@app.post("/run")
async def run_task(
    thread_id: str = Form(...),
    prompt: str = Form(...),
    provider: str | None = Form(default=None),
    files: list[UploadFile] | None = File(default=None),
):
    """DeerFlow üzerinde bir görev başlatır ve sonucu döner."""
    REQUEST_COUNT.labels(method="POST", endpoint="/run").inc()
    temp_dir = Path(tempfile.mkdtemp(prefix="deerflow_bridge_"))
    local_paths: list[str] = []

    try:
        with REQUEST_LATENCY.labels(endpoint="/run").time():
            if files:
                for file in files:
                    file_path = temp_dir / file.filename
                    file_path.write_bytes(await file.read())
                    local_paths.append(str(file_path))
                
                # Dosyaları yükle
                CLIENT.upload_files(thread_id, local_paths)

            # Ağır işi thread'de çalıştır
            result = await asyncio.to_thread(
                CLIENT.chat,
                prompt,
                thread_id=thread_id,
                provider=provider,
            )

            return {
                "status": "success",
                "thread_id": thread_id,
                "result": result,
                "uploaded_files": [os.path.basename(p) for p in local_paths],
            }
    except Exception as e:
        logger.error(f"Error in run_task: {e}", exc_info=True)
        ERROR_COUNT.labels(type=type(e).__name__).inc()
        raise HTTPException(status_code=502, detail=f"DeerFlow bridge error: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/stream")
async def stream_task(
    thread_id: str = Form(...),
    prompt: str = Form(...),
    provider: str | None = Form(default=None),
):
    """DeerFlow görevini stream (SSE) olarak yürütür."""
    REQUEST_COUNT.labels(method="POST", endpoint="/stream").inc()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Senkron generator'ı asenkron olarak tüketmek için
            def get_stream():
                return CLIENT.stream(prompt, thread_id=thread_id)

            loop = asyncio.get_running_loop()
            gen = await loop.run_in_executor(None, lambda: CLIENT.stream(prompt, thread_id=thread_id, provider=provider))  # type: ignore

            for event in gen:
                event_type = getattr(event, "type", "message")
                event_data = getattr(event, "data", str(event))
                logger.debug(f"Bridge sending event: {event_type}")
                
                # Token takibi
                if event_type == "end":
                    usage = event_data.get("usage", {}) if isinstance(event_data, dict) else {}
                    TOKEN_COUNT.labels(type="input").inc(usage.get("input_tokens", 0))
                    TOKEN_COUNT.labels(type="output").inc(usage.get("output_tokens", 0))

                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
            
            yield "event: end\ndata: {\"status\": \"completed\"}\n\n"

        except Exception as e:
            logger.error(f"Error in stream_task generator: {e}", exc_info=True)
            ERROR_COUNT.labels(type=type(e).__name__).inc()
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/artifacts/{thread_id}/{filename}")
async def get_artifact(thread_id: str, filename: str):
    """Sandbox içerisindeki çıktı dosyalarına erişim sağlar."""
    paths = get_paths()
    # Önce outputs dizinine bak
    output_path = paths.sandbox_outputs_dir(thread_id) / filename
    if output_path.exists() and output_path.is_file():
        return FileResponse(output_path)
    
    # Sonra workspace dizinine bak
    work_path = paths.sandbox_work_dir(thread_id) / filename
    if work_path.exists() and work_path.is_file():
        return FileResponse(work_path)
    
    raise HTTPException(status_code=404, detail="Artifact not found")


@app.get("/artifacts/{thread_id}")
async def list_artifacts(thread_id: str):
    """Belirli bir thread için oluşturulan tüm dosyaları listeler."""
    paths = get_paths()  # type: ignore
    outputs = []
    
    out_dir = paths.sandbox_outputs_dir(thread_id)  # type: ignore
    if out_dir.exists():
        outputs.extend([f.name for f in out_dir.iterdir() if f.is_file()])
        
    work_dir = paths.sandbox_work_dir(thread_id)  # type: ignore
    if work_dir.exists():
        outputs.extend([f.name for f in work_dir.iterdir() if f.is_file()])
        
    return {"thread_id": thread_id, "artifacts": sorted(list(set(outputs)))}


@app.post("/cancel/{thread_id}")
async def cancel_task(thread_id: str):
    """DeerFlow thread'ini iptal eder."""
    REQUEST_COUNT.labels(method="POST", endpoint="/cancel").inc()
    try:
        # DeerFlowClient cancel desteği varsa kullan
        if hasattr(CLIENT, "cancel"):
            result = await asyncio.to_thread(CLIENT.cancel, thread_id)
            logger.info(f"Thread cancelled: {thread_id}")
            return {"cancelled": True, "thread_id": thread_id, "result": str(result)}
        else:
            logger.warning(f"Cancel requested for {thread_id} but client does not support cancel.")
            return {"cancelled": False, "thread_id": thread_id, "reason": "client_unsupported"}
    except Exception as e:
        logger.error(f"Cancel error for {thread_id}: {e}", exc_info=True)
        ERROR_COUNT.labels(type="cancel_error").inc()
        raise HTTPException(status_code=500, detail=f"Cancel error: {e}")
