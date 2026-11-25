from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)
