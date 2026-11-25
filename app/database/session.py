from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Pool sized conservatively for hosted free-tier Postgres (e.g. Neon):
# - pool_pre_ping drops connections killed while the DB was suspended/idle
# - pool_recycle avoids keeping connections open across provider timeouts
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=5,
)

if settings.database_url.startswith("postgresql"):
    # Neon's pooled endpoint shares backend sessions and preserves session
    # state between clients: a leftover search_path (e.g. set_config from
    # pg_dump) can leak into our connections. Startup options like
    # -csearch_path are rejected by the pooler, so we pin the schema with a
    # plain SET on every checkout instead.
    @event.listens_for(engine, "checkout")
    def _pin_search_path(dbapi_connection, _connection_record, _connection_proxy):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET search_path TO public")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
