from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Iterable, Dict, Any, AsyncGenerator

import httpx  # type: ignore


class DeerFlowBridgeClient:
    """DeerFlow Bridge servisine istek atan istemci (Refined)."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("DEERFLOW_BRIDGE_URL", "http://deerflow-bridge:8010")).rstrip("/")

    async def run(
        self,
        thread_id: str,
        prompt: str,
        file_paths: Iterable[str] | None = None,
        provider: str | None = None,
    ) -> Dict[str, Any]:
        """DeerFlow Bridge üzerinde bir görev çalıştırır (Bloklayan)."""
        data = {"thread_id": thread_id, "prompt": prompt}
        if provider:
            data["provider"] = provider
        files = []
        opened_files = []

        try:
            if file_paths:
                for path in file_paths:
                    p = Path(path)
                    if not p.exists():
                        continue
                    f = p.open("rb")
                    opened_files.append(f)
                    files.append(("files", (p.name, f, "application/octet-stream")))

            async with httpx.AsyncClient(timeout=1800) as client:
                response = await client.post(
                    f"{self.base_url}/run",
                    data=data,
                    files=files if files else None,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            for f in opened_files:
                f.close()
        
        return {"status": "error", "message": "Unknown execution flow error"}

    async def stream_run(
        self,
        thread_id: str,
        prompt: str,
        provider: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """DeerFlow Bridge üzerinde bir görev çalıştırır (Streaming SSE)."""
        data = {"thread_id": thread_id, "prompt": prompt}
        if provider:
            data["provider"] = provider
        
        try:
            async with httpx.AsyncClient(timeout=1800) as client:
                async with client.stream("POST", f"{self.base_url}/stream", data=data) as response:
                    response.raise_for_status()
                    
                    current_event = None
                    async for line in response.aiter_lines():
                        if line.startswith("event: "):
                            current_event = line[7:].strip()
                        elif line.startswith("data: ") and current_event:
                            data_str = line[6:].strip()
                            try:
                                yield {"event": current_event, "data": json.loads(data_str)}
                            except json.JSONDecodeError:
                                yield {"event": "error", "data": {"message": "Invalid JSON in stream"}}
                            current_event = None
        except Exception as e:
            yield {"event": "error", "data": {"message": str(e)}}

    async def cancel(self, thread_id: str) -> Dict[str, Any]:
        """DeerFlow thread'ini iptal eder."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{self.base_url}/cancel/{thread_id}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"cancelled": False, "error": str(e)}

    async def list_artifacts(self, thread_id: str) -> Dict[str, Any]:
        """Belirli bir thread için üretilen dosyaları listeler."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.base_url}/artifacts/{thread_id}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"thread_id": thread_id, "artifacts": [], "error": str(e)}

    async def check_capabilities(self) -> Dict[str, Any]:
        """Bridge'in desteklediği yetenekleri sorgular."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/capabilities")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def normalize_run_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Faz 12.1: Farklı asistanlardan dönen sonuçları standardize eder."""
        if not result:
            return {}
        
        if isinstance(result, str):
            return {"response": result}
            
        normalized = {}
        
        # Metin yanıtı
        normalized["response"] = result.get("response") or result.get("text") or result.get("content") or ""
        
        # Kullanım metrikleri
        usage = result.get("usage", {})
        if isinstance(usage, dict):
            normalized["input_tokens"] = usage.get("prompt_tokens", usage.get("input_tokens", 0))
            normalized["output_tokens"] = usage.get("completion_tokens", usage.get("output_tokens", 0))
        
        normalized["raw"] = result
        return normalized

    @staticmethod
    def normalize_stream_payload(event: str, data: Dict[str, Any]) -> str:
        """Faz 12.1: Stream verilerindeki farklı text yapılarını ayıklar."""
        if event == "message":
            return data.get("content", data.get("text", ""))
        elif event == "chunk":
            return data.get("delta", data.get("content", ""))
        return ""
