from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.database.session import engine

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Lightweight liveness probe — used by the platform health check."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness_check():
    """Readiness probe — verifies the database connection without leaking details."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="not ready",
        ) from None
    return {"status": "ready"}
