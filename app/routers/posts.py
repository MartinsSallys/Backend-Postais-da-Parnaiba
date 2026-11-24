import re
import unicodedata
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.admin import Admin
from app.models.post import ContentStatus, Post, PostCategory
from app.routers.deps import get_current_admin
from app.schemas.pagination import PaginatedResponse
from app.schemas.post import PostCreate, PostResponse, PostUpdate

router = APIRouter(prefix="/posts", tags=["Posts"])


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "post"


def generate_unique_slug(db: Session, title: str, post_id: int | None = None) -> str:
    base_slug = slugify(title)
    slug = base_slug
    suffix = 2

    while True:
        query = db.query(Post).filter(Post.slug == slug)
        if post_id is not None:
            query = query.filter(Post.id != post_id)
        if query.first() is None:
            return slug
        slug = f"{base_slug}-{suffix}"
        suffix += 1


def apply_status_transition(
    post: Post, new_status: str, publicado_em: datetime | None
) -> None:
    post.status = new_status
    if new_status == "published" and publicado_em is None:
        post.publicado_em = datetime.now(UTC)
    elif new_status == "draft":
        post.publicado_em = None
    elif new_status == "archived":
        pass
    elif new_status == "scheduled":
        if publicado_em is not None:
            post.publicado_em = publicado_em
        else:
            post.publicado_em = None


@router.get("", response_model=PaginatedResponse[PostResponse])
def list_posts(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
    categoria: PostCategory | None = None,
    status_filter: Annotated[
        ContentStatus | None, Query(alias="status")
    ] = None,
    publicados_only: Annotated[bool, Query()] = False,
):
    query = db.query(Post)

    if publicados_only:
        now = datetime.now(UTC)
        query = query.filter(
            Post.status == "published",
            Post.publicado_em <= now,
        )
    elif status_filter is not None:
        query = query.filter(Post.status == status_filter.value)

    if categoria is not None:
        query = query.filter(Post.categoria == categoria)

    query = query.order_by(Post.criado_em.desc())
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {"items": items, "page": page, "size": size, "total": total}


@router.get("/{identifier}", response_model=PostResponse)
def get_post(identifier: str, db: Annotated[Session, Depends(get_db)]):
    post = None
    if identifier.isdigit():
        post = db.query(Post).filter(Post.id == int(identifier)).first()
    if post is None:
        post = db.query(Post).filter(Post.slug == identifier).first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post nao encontrado"
        )
    return post


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[Admin, Depends(get_current_admin)],
):
    post = Post(**payload.model_dump(), slug=generate_unique_slug(db, payload.titulo))

    if post.status == "published" and post.publicado_em is None:
        post.publicado_em = datetime.now(UTC)

    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    payload: PostUpdate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[Admin, Depends(get_current_admin)],
):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post nao encontrado"
        )

    data = payload.model_dump(exclude_unset=True)

    if "status" in data:
        new_status = data["status"]
        publicado_em = data.get("publicado_em")
        apply_status_transition(post, new_status, publicado_em)
        del data["status"]
        if "publicado_em" in data:
            del data["publicado_em"]

    for field, value in data.items():
        setattr(post, field, value)

    if "titulo" in data:
        post.slug = generate_unique_slug(db, data["titulo"], post_id=post.id)

    post.atualizado_em = datetime.now(UTC)
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[Admin, Depends(get_current_admin)],
):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post nao encontrado"
        )

    db.delete(post)
    db.commit()
