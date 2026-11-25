import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.testclient import TestClient

from app.core.security import verify_password
from app.main import app
from app.models.admin import Admin
from app.routers.auth import change_password, login
from app.schemas.auth import LoginRequest, PasswordChangeRequest

client = TestClient(app)


def _make_request(path: str = "/auth/login") -> Request:
    return Request(scope={"type": "http", "method": "POST", "path": path})


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


def test_change_password_updates_hash(db_session: Session, admin: Admin):
    payload = PasswordChangeRequest(
        current_password="secret123", new_password="nova-senha-forte"
    )
    change_password(_make_request("/auth/change-password"), payload, admin, db_session)
    db_session.refresh(admin)

    assert verify_password("nova-senha-forte", admin.hashed_password)
    assert not verify_password("secret123", admin.hashed_password)


def test_change_password_with_wrong_current_returns_400(
    db_session: Session, admin: Admin
):
    with pytest.raises(HTTPException) as exc_info:
        payload = PasswordChangeRequest(
            current_password="senha-errada", new_password="nova-senha-forte"
        )
        change_password(
            _make_request("/auth/change-password"), payload, admin, db_session
        )

    assert exc_info.value.status_code == 400


def test_change_password_rejects_short_new_password():
    with pytest.raises(ValidationError):
        PasswordChangeRequest(current_password="x", new_password="curta")
