import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_db
from .auth import get_current_user
from db.models import Session
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from db.models import Game

logger = logging.getLogger(__name__)

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
        logger.exception("Failed to start session")
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
    session_obj.ended_at = datetime.utcnow()
    try:
        await db.commit()
        return {"status" : "ended"}
    except Exception as e:
        logger.exception("Failed to end session %s", session_id)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.get("/sessions/stats")
async def getStats(period: str = "weekly", db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    now = datetime.utcnow()
    if period == "weekly":
        cutoff = now - timedelta(days=7)
    elif period == "monthly":
        cutoff = now - timedelta(days=30)
    else:
        cutoff = None

    query = select(Game.canonical_name, func.sum(Session.ended_at - Session.started_at)).join(Game, Session.game_id == Game.id).where(Session.user_id == current_user, Session.ended_at != None)
    if cutoff:
        query = query.where(Session.started_at >= cutoff)
    query = query.group_by(Game.canonical_name)

    result = await db.execute(query)
    rows = result.all()
    return [{"game_name": name, "hours": round(duration.total_seconds() / 3600, 2)} for name, duration in rows]
