from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PostCategory(StrEnum):
    cronica = "cronica"
    noticia = "noticia"
    manchete = "manchete"
    estudo = "estudo"


class ContentStatus(StrEnum):
    draft = "draft"
    scheduled = "scheduled"
    published = "published"
    archived = "archived"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(220), index=True)
    slug: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    autor: Mapped[str] = mapped_column(String(120))
    categoria: Mapped[PostCategory] = mapped_column(
        Enum(PostCategory, native_enum=False), index=True
    )
    resumo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subtitulo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    conteudo: Mapped[str] = mapped_column(Text)
    imagem_capa_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
    )
    publicado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
