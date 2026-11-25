from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Pool sized conservatively for hosted free-tier Postgres (e.g. Neon):
# - pool_pre_ping drops connections killed while the DB was suspended/idle
# - pool_recycle avoids keeping connections open across provider timeouts
# - options=-csearch_path=public pins the schema search path on every
#   connection: Neon pooled endpoints share backend sessions and leftover
#   session state (e.g. from pg_dump) can leak between clients
_connect_args = (
    {"options": "-csearch_path=public"}
    if settings.database_url.startswith("postgresql")
    else {}
)
engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=5,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
