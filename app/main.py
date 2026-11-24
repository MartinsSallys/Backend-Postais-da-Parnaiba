import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter
from app.routers import auth, health, postais, posts, timeline_events, upload

logger = logging.getLogger(__name__)


def create_app(create_db_on_startup: bool = True) -> FastAPI:
    """Application factory — used for both production and testing."""
    api = FastAPI(
        title=settings.project_name,
        redirect_slashes=False,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
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

    # --- Static files (uploaded images)
    os.makedirs(settings.upload_dir, exist_ok=True)
    api.mount("/static", StaticFiles(directory="static"), name="static")

    # --- Database initialization (skip in tests)
    if create_db_on_startup:

        @api.on_event("startup")
        def startup_tasks() -> None:
            _init_database()
            _ensure_admin_exists()

    return api


def _init_database() -> None:
    """Create all tables if they don't exist."""
    from app.database.base import Base
    from app.database.session import engine

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")


def _ensure_admin_exists() -> None:
    """Create the admin user from environment variables if it doesn't exist."""
    from app.core.security import get_password_hash
    from app.database.session import SessionLocal
    from app.models.admin import Admin

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
