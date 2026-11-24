from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.database.base import Base
from app.models.admin import Admin


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        session.add(
            Admin(username="admin", hashed_password=get_password_hash("secret123"))
        )
        session.commit()
        yield session

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def admin(db_session: Session) -> Admin:
    return db_session.query(Admin).filter(Admin.username == "admin").one()
