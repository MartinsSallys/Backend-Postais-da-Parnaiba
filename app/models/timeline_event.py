from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitulo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_evento: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    imagem_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    link_externo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    publicado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
