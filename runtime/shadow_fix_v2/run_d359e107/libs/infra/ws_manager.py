"""
libs/infra/ws_manager.py — Phase 13.04
Broadcasts real-time events to the Refine Control Plane.
"""
from __future__ import annotations

import json
from typing import Dict, List
from fastapi import WebSocket

from services.observability.logging import get_logger

logger = get_logger("infra.ws")

class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Support for targeted updates (e.g. specific project)
        self.project_rooms: Dict[str, List[WebSocket]] = {}

    @property
    def client_count(self) -> int:
        """Returns the number of active subscriptions."""
        return len(self.active_connections)

    async def connect(self, websocket: WebSocket, project_id: str | None = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if project_id:
            if project_id not in self.project_rooms:
                self.project_rooms[project_id] = []
            self.project_rooms[project_id].append(websocket)
        logger.debug(f"[WS] New connection accepted. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, project_id: str | None = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if project_id and project_id in self.project_rooms:
            if websocket in self.project_rooms[project_id]:
                self.project_rooms[project_id].remove(websocket)
        logger.debug(f"[WS] Connection closed. Total remaining: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict | str):
        """Sends a message to all connected clients."""
        if isinstance(message, dict):
            message = json.dumps(message)
            
        logger.debug(f"[WS] Broadcasting to {len(self.active_connections)} clients: {message[:100]}...")
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_event(self, event_type: str, component: str, rationale: str, severity: str = "info", category: str = "workflow", summary: Optional[str] = None):
        """Standardized event broadcast for the Dashboard."""
        from datetime import datetime, timezone
        ev = {
            "seq": int(datetime.now(timezone.utc).timestamp() * 1000),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "severity": severity,
            "category": category,
            "message": f"[{component}] {summary or rationale}"
        }
        await self.broadcast(ev)


    async def broadcast_to_project(self, project_id: str, message: dict | str):
        """Sends a message to clients watching a specific project."""
        if project_id not in self.project_rooms:
            return

        if isinstance(message, dict):
            message = json.dumps(message)

        disconnected = []
        for connection in self.project_rooms[project_id]:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn, project_id)

# Singleton instance
ws_manager = ConnectionManager()
