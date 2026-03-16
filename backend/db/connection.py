import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

database_url =  os.getenv("DATABASE_URL")

engine = create_async_engine(database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)