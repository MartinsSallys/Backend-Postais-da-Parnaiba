import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import inspect

from app.core.config import settings
from app.core.rate_limit import limiter
from app.routers import auth, health, postais, posts, timeline_events, upload

logger = logging.getLogger(__name__)


def create_app(run_startup_tasks: bool = True) -> FastAPI:
    """Application factory — used for both production and testing."""

    @asynccontextmanager
    async def lifespan(_api: FastAPI) -> AsyncGenerator[None]:
        if run_startup_tasks:
            _ensure_admin_exists()
        yield

    api = FastAPI(
        title=settings.project_name,
        redirect_slashes=False,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # --- Middleware
    api.state.limiter = limiter
    api.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers
    api.include_router(auth.router)
    api.include_router(postais.router)
    api.include_router(posts.router)
    api.include_router(timeline_events.router)
    api.include_router(upload.router)
    api.include_router(health.router)  # Health check endpoint

    # --- Static files (local dev uploads; Cloudinary is used in production)
    os.makedirs(settings.upload_dir, exist_ok=True)
    api.mount("/static", StaticFiles(directory="static"), name="static")

    return api


def _ensure_admin_exists() -> None:
    """Create the admin user from environment variables if it doesn't exist.

    Skipped (with a warning) when the database hasn't been migrated yet —
    schema management is owned by Alembic, not by app startup.
    """
    from app.core.security import get_password_hash
    from app.database.session import SessionLocal, engine
    from app.models.admin import Admin

    try:
        has_admins_table = inspect(engine).has_table("admins")
    except Exception:
        logger.exception(
            "Could not reach the database during startup. "
            "Admin bootstrap skipped; /health/ready reports the real state."
        )
        return

    if not has_admins_table:
        logger.warning(
            "Table 'admins' not found. Run 'alembic upgrade head' "
            "to apply database migrations."
        )
        return

    username = settings.admin_username.strip()
    password = settings.admin_password.strip()

    if not username or not password:
        return

    with SessionLocal() as db:
        existing = db.query(Admin).filter(Admin.username == username).first()
        if existing is None:
            admin = Admin(
                username=username,
                hashed_password=get_password_hash(password),
            )
            db.add(admin)
            db.commit()
            logger.info("Admin '%s' created automatically.", username)


app = create_app()
