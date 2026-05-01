from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.persona import Persona
from typing import Optional


MAX_PERSONA_PER_USER = 5


class PersonaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, persona_name: Optional[str], persona_description: Optional[str]) -> dict:
        count_result = await self.db.execute(
            select(Persona).where(Persona.user_id == user_id, Persona.delete_flag == 0)
        )
        existing = count_result.scalars().all()
        if len(existing) >= MAX_PERSONA_PER_USER:
            return {"success": False, "message": f"最多创建{MAX_PERSONA_PER_USER}个人设，请删除后再试"}

        persona = Persona(
            user_id=user_id,
            persona_name=persona_name,
            persona_description=persona_description,
        )
        self.db.add(persona)
        await self.db.commit()
        await self.db.refresh(persona)

        return {"success": True, "persona": persona}

    async def list(self, user_id: int) -> list[Persona]:
        result = await self.db.execute(
            select(Persona)
            .where(Persona.user_id == user_id, Persona.delete_flag == 0)
            .order_by(Persona.create_time.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, persona_id: int, user_id: int) -> Optional[Persona]:
        result = await self.db.execute(
            select(Persona).where(Persona.id == persona_id, Persona.user_id == user_id, Persona.delete_flag == 0)
        )
        return result.scalar_one_or_none()

    async def update(self, persona_id: int, user_id: int, persona_name: Optional[str], persona_description: Optional[str]) -> dict:
        persona = await self.get_by_id(persona_id, user_id)
        if not persona:
            return {"success": False, "message": "人设不存在"}

        if persona_name is not None:
            persona.persona_name = persona_name
        if persona_description is not None:
            persona.persona_description = persona_description

        await self.db.commit()
        await self.db.refresh(persona)

        return {"success": True, "persona": persona}

    async def delete(self, persona_id: int, user_id: int) -> dict:
        persona = await self.get_by_id(persona_id, user_id)
        if not persona:
            return {"success": False, "message": "人设不存在"}

        persona.delete_flag = 1
        await self.db.commit()

        return {"success": True, "message": "删除成功"}
