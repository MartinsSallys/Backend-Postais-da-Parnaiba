import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.routers.postais import (
    create_postal,
    delete_postal,
    get_postal,
    list_postais,
    update_postal,
)
from app.schemas.postal import PostalCreate, PostalUpdate


def test_postal_crud(db_session: Session, admin: Admin):
    payload = {
        "titulo": "Porto das Barcas",
        "descricao": "Registro historico do Porto das Barcas.",
        "imagem_url": "https://example.com/porto.jpg",
        "epoca": "Anos 1940",
        "localizacao": "Parnaiba, PI",
    }

    created = create_postal(PostalCreate(**payload), db_session, admin)
    assert created.titulo == payload["titulo"]

    page = list_postais(db_session, page=1, size=10)
    assert page["total"] == 1

    found = get_postal(created.id, db_session)
    assert found.id == created.id

    updated = update_postal(
        created.id,
        PostalUpdate(titulo="Porto das Barcas restaurado"),
        db_session,
        admin,
    )
    assert updated.titulo == "Porto das Barcas restaurado"

    delete_postal(created.id, db_session, admin)

    with pytest.raises(HTTPException) as exc_info:
        get_postal(created.id, db_session)

    assert exc_info.value.status_code == 404


def test_postal_missing_update_returns_404(db_session: Session, admin: Admin):
    with pytest.raises(HTTPException) as exc_info:
        update_postal(999, PostalUpdate(titulo="Nao existe"), db_session, admin)

    assert exc_info.value.status_code == 404
