import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.routers.timeline_events import (
    create_event,
    delete_event,
    get_event,
    list_events,
    update_event,
)
from app.schemas.timeline_event import TimelineEventCreate, TimelineEventUpdate


def test_timeline_event_crud(db_session: Session, admin: Admin):
    payload = {
        "titulo": "Fundacao de Parnaiba",
        "data_evento": "1844-03-25",
        "descricao": "Fundacao da cidade de Parnaiba.",
        "ordem": 1,
        "publicado": True,
    }

    created = create_event(TimelineEventCreate(**payload), db_session, admin)
    assert created.titulo == payload["titulo"]
    assert created.ordem == 1

    page = list_events(page=1, size=10, db=db_session)
    assert page.total == 1

    found = get_event(created.id, db_session)
    assert found.id == created.id

    updated = update_event(
        created.id,
        TimelineEventUpdate(titulo="Fundacao da Cidade", ordem=2),
        db_session,
        admin,
    )
    assert updated.titulo == "Fundacao da Cidade"
    assert updated.ordem == 2

    delete_event(created.id, db_session, admin)

    with pytest.raises(HTTPException) as exc_info:
        get_event(created.id, db_session)

    assert exc_info.value.status_code == 404


def test_timeline_event_missing_update_returns_404(db_session: Session, admin: Admin):
    with pytest.raises(HTTPException) as exc_info:
        update_event(999, TimelineEventUpdate(titulo="Nao existe"), db_session, admin)

    assert exc_info.value.status_code == 404
