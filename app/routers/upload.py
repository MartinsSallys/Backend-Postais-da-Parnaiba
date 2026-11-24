from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.models.admin import Admin
from app.routers.deps import get_current_admin

router = APIRouter(prefix="/upload", tags=["Upload"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_image(
    _admin: Annotated[Admin, Depends(get_current_admin)],
    file: Annotated[UploadFile, File(...)],
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie uma imagem JPEG, PNG, WEBP ou GIF",
        )

    content = file.file.read()
    if len(content) > settings.upload_max_size:
        max_mb = settings.upload_max_size // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o limite de {max_mb}MB",
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(file.filename or "").suffix.lower()
    filename = f"{uuid4().hex}{extension}"
    destination = upload_dir / filename

    with destination.open("wb") as output:
        output.write(content)

    public_prefix = settings.public_upload_prefix.rstrip("/")
    return {"url": f"{public_prefix}/{filename}"}
