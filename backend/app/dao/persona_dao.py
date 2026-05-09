from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.base_dao import BaseDAO
from app.models.persona import Persona


class PersonaDAO(BaseDAO[Persona]):
    def __init__(self):
        super().__init__(Persona)

    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[Persona]:
        try:
            result = await db.execute(
                select(Persona).where(Persona.user_id == user_id)
            )
            return list(result.scalars().all())
        except Exception as e:
            return []

    async def get_by_id_and_user(self, db: AsyncSession, persona_id: int, user_id: int) -> Optional[Persona]:
        try:
            result = await db.execute(
                select(Persona).where(
                    and_(Persona.id == persona_id, Persona.user_id == user_id)
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            return None

    async def create(self, db: AsyncSession, persona: Persona) -> Optional[Persona]:
        return await super().create(db, persona)

    async def update(self, db: AsyncSession, persona_id: int, user_id: int, **kwargs) -> Optional[Persona]:
        try:
            persona = await self.get_by_id_and_user(db, persona_id, user_id)
            if not persona:
                return None
            for key, value in kwargs.items():
                if hasattr(persona, key):
                    setattr(persona, key, value)
            await db.commit()
            await db.refresh(persona)
            return persona
        except Exception as e:
            await db.rollback()
            return None

    async def delete(self, db: AsyncSession, persona_id: int, user_id: int) -> bool:
        try:
            persona = await self.get_by_id_and_user(db, persona_id, user_id)
            if not persona:
                return False
            await db.delete(persona)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            return False


persona_dao = PersonaDAO()