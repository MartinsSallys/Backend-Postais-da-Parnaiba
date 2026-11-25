from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.admin import Admin
from app.routers.deps import get_current_admin
from app.services.media import store_image, validate_image

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_image(
    _admin: Annotated[Admin, Depends(get_current_admin)],
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
):
    content = file.file.read()
    validate_image(file.content_type, content)

    url = store_image(db, file.filename, content)
    return {"url": url}
