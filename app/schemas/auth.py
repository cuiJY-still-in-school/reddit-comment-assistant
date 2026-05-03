from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CookieLoginRequest(BaseModel):
    username: str
    cookie: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    auth_method: str
    last_login_at: str | None = None

    model_config = {"from_attributes": True}


TokenResponse.model_rebuild()
