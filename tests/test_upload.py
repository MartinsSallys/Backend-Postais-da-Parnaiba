from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.routers.upload import upload_image


def _make_admin():
    admin = MagicMock(spec=Admin)
    admin.id = 1
    admin.username = "admin"
    return admin


def _make_upload_file(filename: str, content_type: str, content: bytes):
    file = MagicMock()
    file.filename = filename
    file.content_type = content_type
    file.file.read.return_value = content
    return file


def test_upload_image_creates_file(tmp_path: Path, db_session: Session):
    admin = _make_admin()
    upload_file = _make_upload_file(
        "test.png", "image/png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    )

    with patch("app.routers.upload.settings") as mock_settings:
        mock_settings.upload_dir = str(tmp_path)
        mock_settings.public_upload_prefix = "/static/uploads"
        mock_settings.upload_max_size = 10 * 1024 * 1024

        result = upload_image(admin, upload_file)

    assert "url" in result
    assert result["url"].startswith("/static/uploads/")


def test_upload_invalid_content_type():
    admin = _make_admin()
    upload_file = _make_upload_file("test.txt", "text/plain", b"not an image")

    with pytest.raises(Exception) as exc_info:
        upload_image(admin, upload_file)

    assert "JPEG, PNG, WEBP ou GIF" in str(exc_info.value.detail)


def test_upload_oversized_file(tmp_path: Path):
    admin = _make_admin()
    large_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * (11 * 1024 * 1024)
    upload_file = _make_upload_file("huge.png", "image/png", large_content)

    with patch("app.routers.upload.settings") as mock_settings:
        mock_settings.upload_dir = str(tmp_path)
        mock_settings.public_upload_prefix = "/static/uploads"
        mock_settings.upload_max_size = 10 * 1024 * 1024

        with pytest.raises(Exception) as exc_info:
            upload_image(admin, upload_file)

    assert "10MB" in str(exc_info.value.detail)
