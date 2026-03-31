from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_db
from .auth import get_current_user
from db.models import Device


class RegisterDeviceRequest(BaseModel):
    name: str
    os: str
router = APIRouter()


@router.post("/devices/register")
async def registerDevice(request: RegisterDeviceRequest, db: AsyncSession = Depends(get_db), 
                         current_user: int = Depends(get_current_user)):
    device = Device(user_id=current_user, name=request.name, os=request.os)
    try:
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return device.id
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


