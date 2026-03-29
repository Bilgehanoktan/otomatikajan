"""
WebSocket Yayın Yöneticisi — gerçek event push
"""

import json
from datetime import datetime, timezone
from fastapi import WebSocket


class BroadcastManager:
    def __init__(self):
        self._clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._clients:
            self._clients.remove(ws)

    async def broadcast(self, payload: dict):
        if not self._clients:
            return
        msg = json.dumps(payload, ensure_ascii=False, default=str)
        dead = []
        for ws in self._clients:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def emit(self, event_type: str, agent_id: str, severity: str,
                   phase: str, message: str, **extra):
        await self.broadcast({
            "event":     event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id":  agent_id,
            "severity":  severity,
            "phase":     phase,
            "message":   message,
            **extra,
        })

    async def broadcast_patch(self, job_id: str, file_path: str, diff: str, status: str = "generating"):
        """Canlı patch önizlemesi için yayın yap."""
        await self.broadcast({
            "event": "live_patch",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_id": job_id,
            "file_path": file_path,
            "diff": diff,
            "status": status
        })

    async def broadcast_debate_state(self, debate_id: str, state: str, agent_id: str = "", round_idx: int = 0, **extra):
        """Münazara durumu (thinking, speaking, complete) için yayın yap."""
        await self.broadcast({
            "event": "debate_state",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "debate_id": debate_id,
            "state": state,
            "agent_id": agent_id,
            "round": round_idx,
            **extra
        })

    async def broadcast_job_progress(self, job_id: str, status: str, message: str, **extra):
        """Job ilerlemesini canlı yayınla."""
        await self.broadcast({
            "event": "job_progress",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_id": job_id,
            "status": status,
            "message": message,
            **extra
        })

    @property
    def client_count(self) -> int:
        return len(self._clients)


ws_manager = BroadcastManager()
