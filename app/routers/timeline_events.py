from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.admin import Admin
from app.models.timeline_event import TimelineEvent
from app.routers.deps import get_current_admin
from app.schemas.pagination import PaginatedResponse
from app.schemas.timeline_event import (
    TimelineEventCreate,
    TimelineEventResponse,
    TimelineEventUpdate,
)

router = APIRouter(prefix="/timeline-events", tags=["Timeline Events"])


@router.get("", response_model=PaginatedResponse[TimelineEventResponse])
def list_events(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    publicados_only: Annotated[bool, Query()] = False,
):
    query = db.query(TimelineEvent)

    if publicados_only:
        query = query.filter(TimelineEvent.publicado)

    total = query.count()
    items = (
        query.order_by(TimelineEvent.ordem, TimelineEvent.data_evento.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/{event_id}", response_model=TimelineEventResponse)
def get_event(event_id: int, db: Annotated[Session, Depends(get_db)]):
    event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado",
        )
    return event


@router.post(
    "",
    response_model=TimelineEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    data: TimelineEventCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[Admin, Depends(get_current_admin)],
):
    event = TimelineEvent(**data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.put("/{event_id}", response_model=TimelineEventResponse)
def update_event(
    event_id: int,
    data: TimelineEventUpdate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[Admin, Depends(get_current_admin)],
):
    event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado",
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[Admin, Depends(get_current_admin)],
):
    event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado",
        )
    db.delete(event)
    db.commit()
