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
