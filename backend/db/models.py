from datetime import datetime
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str] = mapped_column()

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column()
    os: Mapped[str] = mapped_column()

class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column()
    igdb_id: Mapped[int | None] = mapped_column()
    process_names: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    cover_url: Mapped[str | None] = mapped_column()
    is_verified: Mapped[bool] = mapped_column(default=False)

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column()