from fastapi import APIRouter
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter()

@router.post("/register")
async def register(request: RegisterRequest):
    pass

@router.post("/login")
async def login(request: LoginRequest):
    pass