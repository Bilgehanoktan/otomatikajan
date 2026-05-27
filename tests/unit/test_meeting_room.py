# filepath: tests/unit/test_meeting_room.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from agents.meeting_room import MeetingRoom
from services.workflow_api.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_meeting_room_hold_meeting_success():
    """
    MeetingRoom.hold_meeting metodunun başarıyla çalışıp
    seçilen katılımcılarla otonom tartışma raporunu döndüğünü doğrular.
    """
    room = MeetingRoom()
    proposal = "Test mimari önerisi: Tüm backend sunucusunu asenkron yerine senkron yapalım."
    
    # hold_meeting tetikleniyor
    result = await room.hold_meeting(proposal=proposal, participant_ids=["architect", "qa_engineer"])
    
    assert "meeting_id" in result
    assert result["proposal"] == proposal
    assert result["participants"] == ["architect", "qa_engineer"]
    # 2 participants * 3 debate rounds (Thesis, Rebuttal, Synthesis) = 6 messages
    assert len(result["debate"]) == 6
    assert "votes" in result
    assert len(result["votes"]) == 2
    assert "consensus" in result
    assert "final_decision" in result


def test_debate_router_list_participants():
    """
    GET /api/v1/debate/participants endpoint'inin aktif otonom uzmanları
    listelediğini doğrular.
    """
    response = client.get("/api/v1/debate/participants")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        participant = data[0]
        assert "id" in participant
        assert "name" in participant
        assert "role" in participant
        assert "emoji" in participant
        assert "description" in participant


def test_debate_router_hold_meeting_endpoint():
    """
    POST /api/v1/debate/meeting endpoint'inin bir öneriyi alıp
    otonom tartışma raporunu döndüğünü doğrular.
    """
    payload = {
        "proposal": "Test veritabanı performans değişikliği.",
        "participant_ids": ["architect", "qa_engineer", "security"]
    }
    response = client.post("/api/v1/debate/meeting", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "meeting_id" in data
    assert data["proposal"] == payload["proposal"]
    assert "debate" in data
    assert "consensus" in data
    assert "votes" in data
    assert "final_decision" in data


def test_debate_router_websocket_meeting():
    """
    WebSocket /api/v1/debate/meeting endpoint'inin canlı debate akışını
    adım adım stream ettiğini doğrular.
    """
    with client.websocket_connect("/api/v1/debate/meeting") as websocket:
        # Send initial request JSON
        websocket.send_json({
            "proposal": "WebSocket entegrasyonu denemesi.",
            "participant_ids": ["architect", "qa_engineer"]
        })
        
        events = []
        try:
            # Let's read some messages from websocket stream
            # Since MeetingRoom holds artificial delays (0.8s), we receive multiple steps
            for _ in range(20):
                data = websocket.receive_json()
                events.append(data)
                if data.get("type") == "complete":
                    break
        except Exception:
            pass
            
        assert len(events) > 0
        # We expect thoughts and a final complete event
        thought_events = [e for e in events if e.get("type") == "thought"]
        vote_events = [e for e in events if e.get("type") == "vote"]
        complete_events = [e for e in events if e.get("type") == "complete"]
        
        assert len(thought_events) > 0
        assert len(vote_events) > 0
        assert len(complete_events) == 1
        assert "debate" in complete_events[0]["data"]

