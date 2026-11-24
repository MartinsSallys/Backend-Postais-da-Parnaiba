from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PostalBase(BaseModel):
    titulo: str
    descricao: str
    imagem_url: str | None = None
    epoca: str
    localizacao: str | None = None


class PostalCreate(PostalBase):
    pass


class PostalUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    imagem_url: str | None = None
    epoca: str | None = None
    localizacao: str | None = None


class PostalResponse(PostalBase):
    id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
