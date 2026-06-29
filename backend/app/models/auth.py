"""Auth API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SalonInfo(BaseModel):
    """Saloon shop details captured at registration (name, location, etc.)."""

    name: str
    description: str = ""
    address: str
    city: str
    latitude: float
    longitude: float
    phone: str
    chairs: int = Field(default=1, ge=1, le=20)
    photo_url: str | None = None


class RegisterClient(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    phone: str | None = None


class RegisterSalon(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str  # the owner's name
    salon: SalonInfo


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    phone: str | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
    salon_id: int | None = None  # present for saloon accounts


class MeResponse(BaseModel):
    user: UserRead
    salon_id: int | None = None
