from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_db
from .auth import get_current_user
from db.models import Session
from sqlalchemy import select
from datetime import datetime, timezone

class StartSessionRequest(BaseModel):
    game_id: int
    device_id: int

router = APIRouter()

@router.post("/sessions/start")
async def startSession(request: StartSessionRequest, db: AsyncSession = Depends(get_db), 
                       current_user: int = Depends(get_current_user)):
    session = Session(user_id=current_user, game_id=request.game_id, device_id=request.device_id)
    try:
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session.id
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.post("/sessions/{session_id}/heartbeat")
async def heartbeat(session_id: int, current_user: int = Depends(get_current_user)):
    return {"status" : "ok"}

@router.post("/sessions/{session_id}/end")
async def endSession(session_id: int, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    session_result = await db.execute(select(Session).where(Session.id == session_id))
    session_obj = session_result.scalar_one_or_none()
    if session_obj is None:
         raise HTTPException(status_code=404, detail="Session not found")
    session_obj.ended_at = datetime.now(timezone.utc)
    try:
        await db.commit()
        return {"status" : "ended"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
