from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_db
from db.models import Game
from .auth import get_current_user
from sqlalchemy import select

class CreateGameRequest(BaseModel):
    canonical_name: str

class UpdateGameRequest(BaseModel):
    igdb_id: int | None = None
    process_names: list[str] | None = None
    cover_url: str | None = None
    is_verified: bool | None = None
router = APIRouter()

@router.post("/games/create")
async def createGame(request: CreateGameRequest, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    game = Game(canonical_name=request.canonical_name)
    try:
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game.id
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/games/process/{process_name}")
async def getGameByProcess(process_name: str, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    game_result = await db.execute(select(Game).where(Game.process_names.any(process_name)))
    game_obj = game_result.scalar_one_or_none()
    if game_obj is None:
        return None
    return game_obj.id

@router.post("/games/{game_id}/update")
async def updateGame(request: UpdateGameRequest, game_id: int, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    game_result = await db.execute(select(Game).where(Game.id == game_id))
    game_obj = game_result.scalar_one_or_none()
    if game_obj is None:
         raise HTTPException(status_code=404, detail="Game not found")
    if request.igdb_id is not None:
        game_obj.igdb_id = request.igdb_id
    if request.process_names is not None:
        game_obj.process_names = request.process_names
    if request.cover_url is not None:
        game_obj.cover_url = request.cover_url
    if request.is_verified is not None:
        game_obj.is_verified = request.is_verified
    try:
        await db.commit()
        return {"status" : "updated"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/games/unverified")
async def getUnverifiedGames(db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    games_query = await db.execute(select(Game).where(Game.is_verified == False))
    games = games_query.scalars().all()
    return [game.id for game in games]

@router.get("/games/getallgames")
async def getAllGames(db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    games_query = await db.execute(select(Game))
    games = games_query.scalars().all()
    games_to_id = {}
    for game in games:
        if game.process_names is not None:
            for process_name in game.process_names:
                games_to_id[process_name] = game.id
    return games_to_id


