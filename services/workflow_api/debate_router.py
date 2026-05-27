from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from agents.specialist_agents.agent_registry import build_agents
from agents.meeting_room import MeetingRoom

router = APIRouter(tags=["Debate Meeting Room"])

class MeetingRequest(BaseModel):
    proposal: str = Field(..., description="Tartışılacak sistem/kod mimari önerisi")
    participant_ids: List[str] = Field(
        default=["architect", "qa_engineer", "security"],
        description="Toplantıya katılacak otonom uzman ajanların ID'leri"
    )

class ParticipantOut(BaseModel):
    id: str
    name: str
    emoji: str
    role: str
    description: str

@router.get("/participants", response_model=List[ParticipantOut])
async def list_debate_participants():
    """
    Toplantı odasına katılabilecek tüm aktif otonom uzmanları listeler.
    """
    try:
        agents = build_agents()
        return [
            ParticipantOut(
                id=aid,
                name=a.name,
                emoji=getattr(a, "emoji", "🤖"),
                role=a.role_name,
                description=a.system_prompt.split("\n")[0]  # Get first line of prompt as desc
            )
            for aid, a in agents.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ajan listesi yüklenemedi: {str(e)}")

@router.post("/meeting")
async def hold_debate_meeting(req: MeetingRequest):
    """
    Belirtilen otonom uzman ajanlar arasında yapılandırılmış konsensüs toplantısı düzenler.
    """
    try:
        agents = build_agents()
        # Katılımcıların varlığını doğrula
        for pid in req.participant_ids:
            if pid not in agents:
                raise HTTPException(status_code=400, detail=f"Katılımcı bulunamadı veya pasif: {pid}")
        
        room = MeetingRoom()
        result = await room.hold_meeting(proposal=req.proposal, participant_ids=req.participant_ids)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Toplantı gerçekleştirilemedi: {str(e)}")
