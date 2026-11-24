from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimelineEventBase(BaseModel):
    titulo: str
    subtitulo: str | None = None
    data_evento: str
    descricao: str
    imagem_url: str | None = None
    link_externo: str | None = None
    ordem: int = 0
    publicado: bool = True


class TimelineEventCreate(TimelineEventBase):
    pass


class TimelineEventUpdate(BaseModel):
    titulo: str | None = None
    subtitulo: str | None = None
    data_evento: str | None = None
    descricao: str | None = None
    imagem_url: str | None = None
    link_externo: str | None = None
    ordem: int | None = None
    publicado: bool | None = None


class TimelineEventResponse(TimelineEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
    atualizado_em: datetime | None = None
