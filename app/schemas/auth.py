import uuid
from pydantic import BaseModel
from app.models.domain import RoleEnum


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: RoleEnum

    class Config:
        from_attributes = True