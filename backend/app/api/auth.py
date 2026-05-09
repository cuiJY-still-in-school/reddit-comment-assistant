from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.response import Response
from app.middleware.auth_middleware import get_current_user_id


router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.register(req.username, req.email, req.password)

    if not result["success"]:
        return Response.error(message=result["message"], code=result.get("code", 400))

    return Response.success(data=result["data"], message=result["message"], code=result.get("code", 0))


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.email_login(req.email, req.password)

    if not result["success"]:
        return Response.error(message=result["message"], code=result.get("code", 401))

    return Response.success(data=result["data"], message=result["message"], code=result.get("code", 0))


@router.get("/me")
async def get_me(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)

    if not user:
        return Response.error(message="用户不存在", code=404)

    return Response.success(
        data={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "auth_method": user.auth_method,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        },
        message="success",
        code=0
    )