from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.base_dao import BaseDAO
from app.models.style_profile import StyleProfile


class StyleProfileDAO(BaseDAO[StyleProfile]):
    def __init__(self):
        super().__init__(StyleProfile)

    async def get_by_user(self, db: AsyncSession, user_id: int) -> Optional[StyleProfile]:
        try:
            result = await db.execute(
                select(StyleProfile).where(StyleProfile.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            return None

    async def upsert(self, db: AsyncSession, profile: StyleProfile) -> Optional[StyleProfile]:
        try:
            existing = await self.get_by_user(db, profile.user_id)
            if existing:
                for key in ['vocabulary_level', 'tone', 'humor_level', 'emoji_usage',
                           'sentence_length', 'writing_style', 'topic_preferences',
                           'analysis_summary', 'sample_count']:
                    if hasattr(profile, key):
                        setattr(existing, key, getattr(profile, key))
                await db.commit()
                await db.refresh(existing)
                return existing
            else:
                db.add(profile)
                await db.commit()
                await db.refresh(profile)
                return profile
        except Exception as e:
            await db.rollback()
            return None


style_profile_dao = StyleProfileDAO()