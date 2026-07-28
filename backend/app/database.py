from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    return {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}


DATABASE_URL = get_settings().database_url
engine = create_engine(DATABASE_URL, **_engine_kwargs(DATABASE_URL))
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

