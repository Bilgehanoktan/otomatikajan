import httpx
import json
import os
import asyncio
from typing import AsyncGenerator, Any, Dict, List, Optional
from packages.observability.logging import get_logger

logger = get_logger("integrations.deerflow_bridge")

class DeerFlowBridgeClient:
    """
    DeerFlow Bridge Client.
    Connects to the external DeerFlow engine via the configured bridge URL.
    """
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("DEERFLOW_BRIDGE_URL", "http://deerflow-bridge:8010")
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        logger.debug(f"DeerFlowBridgeClient initialized with base_url: {self.base_url}")

    async def run(self, thread_id: str, prompt: str, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sends a standard task to the DeerFlow bridge.
        """
        async with httpx.AsyncClient(timeout=600.0) as client:
            payload = {
                "thread_id": thread_id,
                "prompt": prompt,
                "file_paths": file_paths or []
            }
            try:
                response = await client.post(f"{self.base_url}/run", json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"DeerFlow bridge run failed: {e}")
                return {"status": "error", "message": str(e)}

    async def stream_run(self, thread_id: str, prompt: str, provider: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Sends a streaming task to the DeerFlow bridge.
        """
        async with httpx.AsyncClient(timeout=600.0) as client:
            payload = {
                "thread_id": thread_id,
                "prompt": prompt,
                "provider": provider
            }
            try:
                async with client.stream("POST", f"{self.base_url}/stream", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data:
                                try:
                                    yield json.loads(raw_data)
                                except json.JSONDecodeError:
                                    logger.warning(f"Failed to decode DeerFlow stream event: {raw_data}")
            except Exception as e:
                logger.error(f"DeerFlow bridge stream failed: {e}")
                yield {"event": "error", "data": {"message": str(e)}}
