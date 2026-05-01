from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest, LoginRequest,
    TokenResponse, UserResponse,
)
from app.schemas.common import CommonResponse
from app.middleware.auth_middleware import get_current_user_id


router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=CommonResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.register(req.username, req.email, req.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    user = result["user"]
    return CommonResponse(
        success=True,
        message="注册成功",
        data={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
        },
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.email_login(req.email, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    user = result["user"]
    return TokenResponse(
        access_token=result["token"],
        expires_in=86400,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            auth_method=user.auth_method,
            last_login_at=str(user.last_login_at) if user.last_login_at else None,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        auth_method=user.auth_method,
        last_login_at=str(user.last_login_at) if user.last_login_at else None,
    )
