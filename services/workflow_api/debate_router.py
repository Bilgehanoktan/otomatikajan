from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from agents.specialist_agents.agent_registry import build_agents
from agents.meeting_room import MeetingRoom
from services.observability.logging import get_logger

logger = get_logger("debate_router")

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

@router.websocket("/meeting")
async def websocket_debate_meeting(websocket: WebSocket):
    """
    WebSocket üzerinden canlı ve akan (streaming) ajan debate toplantısı düzenler.
    """
    await websocket.accept()
    logger.info("WebSocket debate meeting: Connection accepted.")
    try:
        # Client sends initial request as JSON containing "proposal" and optional "participant_ids"
        data = await websocket.receive_json()
        proposal = data.get("proposal")
        participant_ids = data.get("participant_ids", ["architect", "qa_engineer", "security"])
        
        if not proposal:
            await websocket.send_json({"type": "error", "message": "Proposal is required."})
            await websocket.close()
            return
            
        agents = build_agents()
        for pid in participant_ids:
            if pid not in agents:
                await websocket.send_json({"type": "error", "message": f"Katılımcı bulunamadı veya pasif: {pid}"})
                await websocket.close()
                return

        # Define async step callback
        async def step_callback(event: Dict[str, Any]):
            try:
                await websocket.send_json(event)
            except Exception as stream_err:
                logger.error(f"WebSocket send error during debate streaming: {str(stream_err)}")
            
        room = MeetingRoom()
        await room.hold_meeting(proposal=proposal, participant_ids=participant_ids, step_callback=step_callback)
        
    except WebSocketDisconnect:
        logger.info("WebSocket debate meeting disconnected by client.")
    except Exception as e:
        logger.error(f"WebSocket debate meeting error: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

