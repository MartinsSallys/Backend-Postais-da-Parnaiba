import secrets
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — loaded from environment variables and .env file."""

    # --- Application
    project_name: str = "Postais da Parnaiba API"
    debug: bool = False

    # --- Database
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/postais_da_parnaiba"
    )

    # --- Security
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- Uploads
    upload_dir: str = "static/uploads"
    public_upload_prefix: str = "/static/uploads"
    upload_max_size: int = 10 * 1024 * 1024  # 10MB

    # --- CORS
    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
    ]

    # --- Admin (auto-create on first startup)
    admin_username: str = ""
    admin_password: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def model_post_init(self, __context: object) -> None:
        """Validate critical settings after initialization."""
        if not self.secret_key:
            # In production, SECRET_KEY must be set explicitly
            # In development, generate a random one with a warning
            if self.debug:
                self.secret_key = secrets.token_hex(32)
                print(
                    "⚠  WARNING: No SECRET_KEY set. Generated a random key. "
                    "Sessions will be lost on restart.",
                    file=sys.stderr,
                )
            else:
                print(
                    "❌ FATAL: SECRET_KEY is required in production.\n"
                    "   Set it in .env or as an environment variable.\n"
                    "   Generate one with: openssl rand -hex 32",
                    file=sys.stderr,
                )
                sys.exit(1)


settings = Settings()
