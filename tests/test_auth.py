import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.testclient import TestClient

from app.main import app
from app.routers.auth import login
from app.schemas.auth import LoginRequest

client = TestClient(app)


def _make_request() -> Request:
    return Request(scope={"type": "http", "method": "POST", "path": "/auth/login"})


def test_login_returns_jwt(db_session: Session):
    payload = LoginRequest(username="admin", password="secret123")
    response = login(_make_request(), payload, db_session)

    assert response.token_type == "bearer"
    assert response.access_token


def test_login_with_invalid_credentials_returns_401(db_session: Session):
    with pytest.raises(HTTPException) as exc_info:
        payload = LoginRequest(username="admin", password="wrong")
        login(_make_request(), payload, db_session)

    assert exc_info.value.status_code == 401
