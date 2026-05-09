from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.user_dao import user_dao
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.utils.cache import cache_set
from app.core.config import settings
from typing import Optional


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, email: str, password: str) -> dict:
        if not username or len(username) < 2:
            return {"success": False, "code": 10001, "message": "用户名至少需要2个字符"}
        if len(username) > 50:
            return {"success": False, "code": 10002, "message": "用户名不能超过50个字符"}
        if not email or "@" not in email:
            return {"success": False, "code": 10003, "message": "邮箱格式不正确"}
        if not password or len(password) < 6:
            return {"success": False, "code": 10004, "message": "密码至少需要6个字符"}

        existing = await user_dao.get_by_email(self.db, email)
        if existing:
            return {"success": False, "code": 10005, "message": "邮箱已被注册"}

        existing = await user_dao.get_by_username(self.db, username)
        if existing:
            return {"success": False, "code": 10006, "message": "用户名已被使用"}

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            auth_method="password",
        )
        result = await user_dao.create(self.db, user)
        if not result:
            return {"success": False, "code": 10007, "message": "创建用户失败"}

        return {
            "success": True,
            "code": 0,
            "message": "注册成功",
            "data": {"user_id": result.id, "username": result.username}
        }

    async def email_login(self, email: str, password: str) -> dict:
        if not email or "@" not in email:
            return {"success": False, "code": 10010, "message": "邮箱格式不正确"}
        if not password:
            return {"success": False, "code": 10011, "message": "密码不能为空"}

        user = await user_dao.get_by_email(self.db, email)
        if not user:
            return {"success": False, "code": 10012, "message": "邮箱或密码错误"}

        if user.status == 0:
            return {"success": False, "code": 10013, "message": "账号已禁用"}

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return {"success": False, "code": 10014, "message": "账号已锁定，请稍后重试"}

        if user.delete_flag == 1:
            return {"success": False, "code": 10015, "message": "该账号已注销"}

        if not user.password_hash:
            return {"success": False, "code": 10016, "message": "该账号使用第三方登录"}

        if not verify_password(password, user.password_hash):
            fail_count = user.login_fail_count + 1
            await user_dao.update_login_fail(self.db, user.id, fail_count if fail_count < 5 else 0)
            if fail_count >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
                await self.db.commit()
            return {"success": False, "code": 10017, "message": "邮箱或密码错误"}

        await user_dao.update_login_fail(self.db, user.id, 0)
        await user_dao.update_last_login(self.db, user.id)

        token = create_access_token(user.id)
        await cache_set(f"token:{user.id}", token, settings.jwt_expiration_minutes * 60)

        return {
            "success": True,
            "code": 0,
            "message": "登录成功",
            "data": {
                "user": {"id": user.id, "email": user.email, "username": user.username},
                "token": token,
                "expires_in": settings.jwt_expiration_minutes * 60
            }
        }

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await user_dao.get_by_id(self.db, user_id)