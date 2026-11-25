import logging
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.upload import Upload

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _sniff_image_type(content: bytes) -> str | None:
    """Return the real image type from magic bytes, or None."""
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:4] == b"GIF8":
        return "image/gif"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(content_type: str | None, content: bytes) -> None:
    """Validate declared type, real content signature and size."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie uma imagem JPEG, PNG, WEBP ou GIF",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo vazio",
        )

    if len(content) > settings.upload_max_size:
        max_mb = settings.upload_max_size // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o limite de {max_mb}MB",
        )

    if _sniff_image_type(content) != content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O conteudo do arquivo nao corresponde a uma imagem valida",
        )


def _configure_cloudinary() -> None:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def store_image(db: Session, filename: str | None, content: bytes) -> str:
    """Persist an image and return its public URL.

    Uses Cloudinary when configured (production) and registers the asset in the
    uploads table; falls back to the local filesystem for development.
    """
    if settings.cloudinary_enabled:
        _configure_cloudinary()
        try:
            result = cloudinary.uploader.upload(
                BytesIO(content),
                folder=settings.cloudinary_folder,
                resource_type="image",
            )
        except Exception:
            logger.exception("Cloudinary upload failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Falha ao enviar a imagem para o armazenamento externo",
            ) from None

        upload = Upload(
            public_id=result["public_id"],
            url=result["secure_url"],
        )
        db.add(upload)
        db.commit()
        return upload.url

    return _store_image_locally(filename, content)


def _store_image_locally(filename: str | None, content: bytes) -> str:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(filename or "").suffix.lower()
    destination = upload_dir / f"{uuid4().hex}{extension}"
    destination.write_bytes(content)

    public_prefix = settings.public_upload_prefix.rstrip("/")
    return f"{public_prefix}/{destination.name}"


def delete_media_by_url(db: Session, url: str | None) -> None:
    """Delete a Cloudinary asset tracked by its public URL.

    No-ops for local/static images. Failures are logged, never raised —
    content deletion should not break because of the media provider.
    """
    if not url:
        return

    upload = db.query(Upload).filter(Upload.url == url).first()
    if upload is None:
        return

    try:
        _configure_cloudinary()
        cloudinary.uploader.destroy(upload.public_id)
    except Exception:
        logger.exception("Failed to delete Cloudinary asset %s", upload.public_id)
        return

    db.delete(upload)
    db.commit()
