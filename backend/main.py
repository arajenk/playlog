from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.models import Base
from db.connection import engine
from routers import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code here
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # shutdown code here (optional)

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)