from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.cache import cache_set, cache_delete, get_redis
from app.config import settings
from typing import Optional


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, email: str, password: str) -> dict:
        existing = await self.db.execute(
            select(User).where((User.email == email) | (User.username == username))
        )
        if existing.scalar_one_or_none():
            return {"success": False, "message": "用户名或邮箱已存在"}

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            auth_method="password",
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return {"success": True, "user": user}

    async def email_login(self, email: str, password: str) -> dict:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            return {"success": False, "message": "邮箱或密码错误"}

        if user.status == 0:
            return {"success": False, "message": "账号已禁用"}

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return {"success": False, "message": "账号已锁定，请稍后重试"}

        if user.delete_flag == 1:
            return {"success": False, "message": "该账号已注销"}

        if not user.password_hash:
            return {"success": False, "message": "该账号使用第三方登录"}

        if not verify_password(password, user.password_hash):
            fail_count = user.login_fail_count + 1
            if fail_count >= 5:
                from datetime import timedelta
                user.login_fail_count = 0
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            else:
                user.login_fail_count = fail_count
            await self.db.commit()
            return {"success": False, "message": "邮箱或密码错误"}

        user.login_fail_count = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        token = create_access_token(user.id)
        await cache_set(f"token:{user.id}", token, settings.jwt_access_token_expire_minutes * 60)

        return {"success": True, "user": user, "token": token}

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
