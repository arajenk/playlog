import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_db
from sqlalchemy import select
from db.models import User
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter()

TOKEN_EXPIRY_DAYS = 90

def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
    payload = {"sub": str(user_id), "exp": exp}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email_result = await db.execute(select(User).where(User.email == request.email))
    user = email_result.scalar_one_or_none()
    if user is not None:
         raise HTTPException(status_code=409, detail="Email already exists")
    
    username_result = await db.execute(select(User).where(User.username == request.username))
    user = username_result.scalar_one_or_none()
    if user is not None:
         raise HTTPException(status_code=409, detail="Username already exists")
    
    hashed_password = pwd_context.hash(request.password)
    user = User(username=request.username, email=request.email, password_hash=hashed_password)
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return create_token(user.id)
    except Exception as e:
        logger.exception("Failed to register user")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    email_result = await db.execute(select(User).where(User.email == request.email))
    user = email_result.scalar_one_or_none()
    if user is None:
         raise HTTPException(status_code=401, detail="Invalid credentials")
    if pwd_context.verify(request.password, user.password_hash) == False:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return create_token(user.id)

async def get_current_user(authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
