from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.admin import Admin
from app.models.postal import Postal
from app.routers.deps import get_current_admin
from app.schemas.pagination import PaginatedResponse
from app.schemas.postal import PostalCreate, PostalResponse, PostalUpdate
from app.services.media import delete_media_by_url

router = APIRouter(prefix="/postais", tags=["Postais"])


@router.get("", response_model=PaginatedResponse[PostalResponse])
def list_postais(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    query = db.query(Postal).order_by(Postal.criado_em.desc(), Postal.id.desc())
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {"items": items, "page": page, "size": size, "total": total}


@router.get("/{postal_id}", response_model=PostalResponse)
def get_postal(postal_id: int, db: Annotated[Session, Depends(get_db)]):
    postal = db.get(Postal, postal_id)
    if postal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Postal nao encontrado"
        )
    return postal


@router.post("", response_model=PostalResponse, status_code=status.HTTP_201_CREATED)
def create_postal(
    payload: PostalCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[Admin, Depends(get_current_admin)],
):
    postal = Postal(**payload.model_dump())
    db.add(postal)
    db.commit()
    db.refresh(postal)
    return postal


@router.put("/{postal_id}", response_model=PostalResponse)
def update_postal(
    postal_id: int,
    payload: PostalUpdate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[Admin, Depends(get_current_admin)],
):
    postal = db.get(Postal, postal_id)
    if postal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Postal nao encontrado"
        )

    old_image_url = postal.imagem_url
    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(postal, field, value)

    db.commit()
    db.refresh(postal)

    if "imagem_url" in data and data["imagem_url"] != old_image_url:
        delete_media_by_url(db, old_image_url)

    return postal


@router.delete("/{postal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_postal(
    postal_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[Admin, Depends(get_current_admin)],
):
    postal = db.get(Postal, postal_id)
    if postal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Postal nao encontrado"
        )

    image_url = postal.imagem_url
    db.delete(postal)
    db.commit()
    delete_media_by_url(db, image_url)
