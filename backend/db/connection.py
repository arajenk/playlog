import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
load_dotenv()
database_url =  os.getenv("DATABASE_URL")

engine = create_async_engine(database_url,
                             connect_args={"statement_cache_size": 0})
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session
