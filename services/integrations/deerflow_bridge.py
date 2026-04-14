import os
import httpx
import json
import asyncio
from typing import Dict, Any, AsyncGenerator, Optional, List
from services.observability.logging import get_logger
from services.integrations.base import BaseIntegrationTool, async_retry

logger = get_logger("integrations.deerflow")

class DeerFlowBridgeClient(BaseIntegrationTool):
    """
    Sovereign AGI - DeerFlow Bridge Adapter
    Standardized connector for heavy reasoning and streaming tasks.
    """
    def __init__(self, base_url: str = None, timeout: float = 300.0):
        super().__init__(tool_name="deerflow")
        self.base_url = (base_url or os.getenv("DEERFLOW_BRIDGE_URL", "http://deerflow-bridge:8010")).rstrip("/")
        self.timeout = timeout

    async def call(self, action: str, **kwargs) -> Any:
        if action == "run":
            return await self.run(**kwargs)
        elif action == "cancel":
            return await self.cancel(**kwargs)
        return None

    @async_retry(max_retries=2, backoff=5.0)
    async def run(self, thread_id: str, prompt: str, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Senkron (beklemeli) görev çalıştırma."""
        url = f"{self.base_url}/run"
        payload = {
            "thread_id": thread_id,
            "prompt": prompt,
            "file_paths": file_paths or []
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"DeerFlow run failed: {e}")
            return {"status": "error", "reason": str(e)}

    async def stream_run(self, thread_id: str, prompt: str, provider: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Akış (streaming) üzerinden görev çalıştırma."""
        url = f"{self.base_url}/stream"
        payload = {
            "thread_id": thread_id,
            "prompt": prompt,
            "provider": provider
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        if line.startswith("data: "):
                            line = line[6:]
                        
                        try:
                            event = json.loads(line)
                            yield event
                        except json.JSONDecodeError:
                            logger.warning(f"Malformed JSON from DeerFlow stream: {line}")
                            continue
        except Exception as e:
            logger.error(f"DeerFlow stream failed: {e}")
            yield {"event": "error", "data": {"message": str(e)}}

    async def cancel(self, job_id: str) -> bool:
        """Çalışan bir işi iptal et."""
        url = f"{self.base_url}/cancel/{job_id}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"DeerFlow cancel failed for {job_id}: {e}")
            return False

def get_deerflow_bridge() -> DeerFlowBridgeClient:
    return DeerFlowBridgeClient()
