from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Postal(Base):
    __tablename__ = "postais"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(180), index=True)
    descricao: Mapped[str] = mapped_column(Text)
    imagem_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    epoca: Mapped[str] = mapped_column(String(120), index=True)
    localizacao: Mapped[str | None] = mapped_column(String(180), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
