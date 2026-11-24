from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.post import ContentStatus
from app.routers.posts import (
    create_post,
    delete_post,
    get_post,
    list_posts,
    update_post,
)
from app.schemas.post import PostCreate, PostUpdate


def test_post_crud_and_unique_slug(db_session: Session, admin: Admin):
    payload = {
        "titulo": "A Parnaiba antiga",
        "autor": "Equipe editorial",
        "categoria": "cronica",
        "conteudo": "# Memoria\nTexto em markdown.",
        "imagem_capa_url": "https://example.com/capa.jpg",
        "status": "draft",
    }

    first = create_post(PostCreate(**payload), db_session, admin)
    assert first.slug == "a-parnaiba-antiga"
    assert first.status == "draft"
    assert first.publicado_em is None

    second = create_post(PostCreate(**payload), db_session, admin)
    assert second.slug == "a-parnaiba-antiga-2"

    page = list_posts(db_session, page=1, size=10, status_filter=ContentStatus.draft)
    assert page["total"] == 2

    found = get_post(first.slug, db_session)
    assert found.id == first.id

    updated = update_post(
        first.id,
        PostUpdate(titulo="Nova Parnaiba antiga", categoria="estudo"),
        db_session,
        admin,
    )
    assert updated.slug == "nova-parnaiba-antiga"
    assert updated.categoria == "estudo"

    delete_post(first.id, db_session, admin)

    with pytest.raises(HTTPException) as exc_info:
        get_post(updated.slug, db_session)

    assert exc_info.value.status_code == 404


def test_post_missing_update_returns_404(db_session: Session, admin: Admin):
    with pytest.raises(HTTPException) as exc_info:
        update_post(999, PostUpdate(titulo="Nao existe"), db_session, admin)

    assert exc_info.value.status_code == 404


def test_post_draft_to_published(db_session: Session, admin: Admin):
    post = create_post(
        PostCreate(
            titulo="Teste Publicacao",
            autor="Admin",
            categoria="noticia",
            conteudo="Conteudo teste.",
            status="draft",
        ),
        db_session,
        admin,
    )
    assert post.status == "draft"
    assert post.publicado_em is None

    updated = update_post(post.id, PostUpdate(status="published"), db_session, admin)
    assert updated.status == "published"
    assert updated.publicado_em is not None


def test_post_draft_to_scheduled(db_session: Session, admin: Admin):
    future = datetime.now(UTC) + timedelta(days=7)
    post = create_post(
        PostCreate(
            titulo="Teste Agendamento",
            autor="Admin",
            categoria="estudo",
            conteudo="Conteudo agendado.",
            status="draft",
        ),
        db_session,
        admin,
    )

    updated = update_post(
        post.id,
        PostUpdate(status="scheduled", publicado_em=future),
        db_session,
        admin,
    )
    assert updated.status == "scheduled"
    assert updated.publicado_em is not None


def test_post_published_to_archived(db_session: Session, admin: Admin):
    post = create_post(
        PostCreate(
            titulo="Teste Arquivamento",
            autor="Admin",
            categoria="cronica",
            conteudo="Conteudo para arquivar.",
            status="published",
        ),
        db_session,
        admin,
    )
    assert post.status == "published"

    updated = update_post(post.id, PostUpdate(status="archived"), db_session, admin)
    assert updated.status == "archived"


def test_public_api_filters_by_status(db_session: Session, admin: Admin):
    create_post(
        PostCreate(
            titulo="Draft Post",
            autor="Admin",
            categoria="cronica",
            conteudo="Rascunho.",
            status="draft",
        ),
        db_session,
        admin,
    )
    create_post(
        PostCreate(
            titulo="Published Post",
            autor="Admin",
            categoria="noticia",
            conteudo="Publicado.",
            status="published",
        ),
        db_session,
        admin,
    )
    create_post(
        PostCreate(
            titulo="Archived Post",
            autor="Admin",
            categoria="estudo",
            conteudo="Arquivado.",
            status="archived",
        ),
        db_session,
        admin,
    )

    public = list_posts(db_session, page=1, size=50, publicados_only=True)
    assert public["total"] == 1
    assert public["items"][0].titulo == "Published Post"

    all_drafts = list_posts(
        db_session, page=1, size=50, status_filter=ContentStatus.draft
    )
    assert all_drafts["total"] == 1
    assert all_drafts["items"][0].titulo == "Draft Post"


def test_existing_data_compatibility(db_session: Session, admin: Admin):
    post = create_post(
        PostCreate(
            titulo="Post existente",
            autor="Admin",
            categoria="cronica",
            conteudo="Conteudo antigo.",
            status="published",
        ),
        db_session,
        admin,
    )
    assert post.status == "published"
    assert post.publicado_em is not None

    found = get_post(post.slug, db_session)
    assert found.resumo is None
    assert found.subtitulo is None
    assert found.atualizado_em is None
