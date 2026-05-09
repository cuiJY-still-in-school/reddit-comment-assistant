from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.base_dao import BaseDAO
from app.models.user import User


class UserDAO(BaseDAO[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            return None

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()
        except Exception as e:
            return None

    async def create(self, db: AsyncSession, user: User) -> Optional[User]:
        return await super().create(db, user)

    async def update_login_fail(self, db: AsyncSession, user_id: int, fail_count: int):
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.login_fail_count = fail_count
                await db.commit()
        except Exception:
            pass

    async def update_last_login(self, db: AsyncSession, user_id: int):
        from datetime import datetime, timezone
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.last_login_at = datetime.now(timezone.utc)
                await db.commit()
        except Exception:
            pass


user_dao = UserDAO()