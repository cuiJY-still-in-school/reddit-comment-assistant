from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.base_dao import BaseDAO
from app.models.style_sample import StyleSample


class StyleSampleDAO(BaseDAO[StyleSample]):
    def __init__(self):
        super().__init__(StyleSample)

    async def get_by_user(self, db: AsyncSession, user_id: int, limit: int = 20, offset: int = 0) -> List[StyleSample]:
        try:
            result = await db.execute(
                select(StyleSample)
                .where(StyleSample.user_id == user_id)
                .order_by(StyleSample.create_time.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
        except Exception as e:
            return []

    async def count_by_user(self, db: AsyncSession, user_id: int) -> int:
        try:
            from sqlalchemy import func
            result = await db.execute(
                select(func.count()).select_from(StyleSample).where(StyleSample.user_id == user_id)
            )
            return result.scalar() or 0
        except Exception:
            return 0

    async def create(self, db: AsyncSession, sample: StyleSample) -> Optional[StyleSample]:
        return await super().create(db, sample)

    async def delete(self, db: AsyncSession, sample_id: int, user_id: int) -> bool:
        try:
            result = await db.execute(
                select(StyleSample).where(
                    and_(StyleSample.id == sample_id, StyleSample.user_id == user_id)
                )
            )
            sample = result.scalar_one_or_none()
            if not sample:
                return False
            await db.delete(sample)
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            return False


style_sample_dao = StyleSampleDAO()