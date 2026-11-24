from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.post import ContentStatus, PostCategory


class PostBase(BaseModel):
    titulo: str
    autor: str
    categoria: PostCategory
    resumo: str | None = None
    subtitulo: str | None = None
    conteudo: str
    imagem_capa_url: str | None = None
    status: ContentStatus = ContentStatus.draft
    publicado_em: datetime | None = None


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    titulo: str | None = None
    autor: str | None = None
    categoria: PostCategory | None = None
    resumo: str | None = None
    subtitulo: str | None = None
    conteudo: str | None = None
    imagem_capa_url: str | None = None
    status: ContentStatus | None = None
    publicado_em: datetime | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    slug: str
    autor: str
    categoria: PostCategory
    resumo: str | None = None
    subtitulo: str | None = None
    conteudo: str
    imagem_capa_url: str | None = None
    status: ContentStatus
    publicado_em: datetime | None = None
    criado_em: datetime
    atualizado_em: datetime | None = None
