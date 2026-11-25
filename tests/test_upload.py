from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.upload import Upload
from app.routers.upload import upload_image

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50


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


def _local_settings(tmp_path: Path) -> MagicMock:
    mock = MagicMock()
    mock.cloudinary_enabled = False
    mock.upload_dir = str(tmp_path)
    mock.public_upload_prefix = "/static/uploads"
    mock.upload_max_size = 10 * 1024 * 1024
    return mock


def test_upload_image_creates_file(tmp_path: Path, db_session: Session):
    admin = _make_admin()
    upload_file = _make_upload_file("test.png", "image/png", PNG_BYTES)

    with patch("app.services.media.settings") as mock_settings:
        mock = _local_settings(tmp_path)
        mock_settings.cloudinary_enabled = mock.cloudinary_enabled
        mock_settings.upload_dir = mock.upload_dir
        mock_settings.public_upload_prefix = mock.public_upload_prefix
        mock_settings.upload_max_size = mock.upload_max_size

        result = upload_image(admin, upload_file, db_session)

    assert "url" in result
    assert result["url"].startswith("/static/uploads/")


def test_upload_image_via_cloudinary(tmp_path: Path, db_session: Session):
    admin = _make_admin()
    upload_file = _make_upload_file("test.png", "image/png", PNG_BYTES)

    fake_result = {
        "public_id": "postais-da-parnaiba/abc123",
        "secure_url": "https://res.cloudinary.com/demo/image/upload/v1/postais-da-parnaiba/abc123.png",
    }

    with (
        patch("app.services.media.settings") as mock_settings,
        patch("app.services.media.cloudinary") as mock_cloudinary,
    ):
        mock_settings.cloudinary_enabled = True
        mock_settings.cloudinary_folder = "postais-da-parnaiba"
        mock_settings.upload_max_size = 10 * 1024 * 1024
        mock_cloudinary.uploader.upload.return_value = fake_result

        result = upload_image(admin, upload_file, db_session)

    assert result["url"] == fake_result["secure_url"]
    assert db_session.query(Upload).count() == 1


def test_upload_invalid_content_type(db_session: Session):
    admin = _make_admin()
    upload_file = _make_upload_file("test.txt", "text/plain", b"not an image")

    with pytest.raises(Exception) as exc_info:
        upload_image(admin, upload_file, db_session)

    assert "JPEG, PNG, WEBP ou GIF" in str(exc_info.value.detail)


def test_upload_spoofed_content_type(db_session: Session):
    admin = _make_admin()
    upload_file = _make_upload_file(
        "evil.png", "image/png", b"this is not really a png"
    )

    with pytest.raises(Exception) as exc_info:
        upload_image(admin, upload_file, db_session)

    assert "nao corresponde" in str(exc_info.value.detail)


def test_upload_empty_file(db_session: Session):
    admin = _make_admin()
    upload_file = _make_upload_file("empty.png", "image/png", b"")

    with pytest.raises(Exception) as exc_info:
        upload_image(admin, upload_file, db_session)

    assert "vazio" in str(exc_info.value.detail)


def test_upload_oversized_file(db_session: Session):
    admin = _make_admin()
    large_content = PNG_BYTES + b"\x00" * (11 * 1024 * 1024)
    upload_file = _make_upload_file("huge.png", "image/png", large_content)

    with pytest.raises(Exception) as exc_info:
        upload_image(admin, upload_file, db_session)

    assert "10MB" in str(exc_info.value.detail)
