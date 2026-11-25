from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.security import create_access_token, get_password_hash, verify_password
from app.database.session import get_db
from app.models.admin import Admin
from app.routers.deps import get_current_admin
from app.schemas.auth import LoginRequest, PasswordChangeRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    admin = db.query(Admin).filter(Admin.username == payload.username).first()
    if admin is None or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario ou senha invalidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(admin.username))


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def change_password(
    request: Request,
    payload: PasswordChangeRequest,
    admin: Annotated[Admin, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    if not verify_password(payload.current_password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta",
        )
    admin.hashed_password = get_password_hash(payload.new_password)
    db.commit()
