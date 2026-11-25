import secrets
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — loaded from environment variables and .env file."""

    # --- Application
    project_name: str = "Postais da Parnaiba API"
    environment: str = "development"  # development | production
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

    # --- Cloudinary (persistent image storage; optional in dev)
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    cloudinary_folder: str = "postais-da-parnaiba"

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

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cloudinary_enabled(self) -> bool:
        return all(
            [
                self.cloudinary_cloud_name,
                self.cloudinary_api_key,
                self.cloudinary_api_secret,
            ]
        )

    def model_post_init(self, __context: object) -> None:
        """Validate critical settings after initialization."""
        if not self.secret_key:
            if self.debug and not self.is_production:
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

        if self.is_production and not self.cloudinary_enabled:
            print(
                "⚠  WARNING: Cloudinary credentials not set. "
                "Image uploads will be stored on the local filesystem, "
                "which is ephemeral on most hosting providers.",
                file=sys.stderr,
            )


settings = Settings()
