from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.persona_dao import persona_dao
from app.models.persona import Persona
from typing import Optional


MAX_PERSONA_PER_USER = 5


class PersonaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, persona_name: Optional[str], persona_description: Optional[str]) -> dict:
        if persona_name and len(persona_name) > 288:
            return {"success": False, "code": 20001, "message": "人设名称不能超过288个字符"}
        if persona_description and len(persona_description) > 5000:
            return {"success": False, "code": 20002, "message": "人设描述不能超过5000个字符"}

        existing = await persona_dao.get_by_user(self.db, user_id)
        if len(existing) >= MAX_PERSONA_PER_USER:
            return {"success": False, "code": 20003, "message": f"最多创建{MAX_PERSONA_PER_USER}个人设，请删除后再试"}

        persona = Persona(
            user_id=user_id,
            persona_name=persona_name,
            persona_description=persona_description,
        )
        result = await persona_dao.create(self.db, persona)
        if not result:
            return {"success": False, "code": 20004, "message": "创建人设失败"}

        return {"success": True, "code": 0, "message": "创建成功", "data": {"persona_id": result.id}}

    async def list(self, user_id: int) -> dict:
        personas = await persona_dao.get_by_user(self.db, user_id)
        return {
            "success": True,
            "code": 0,
            "message": "success",
            "data": [{"id": p.id, "persona_name": p.persona_name, "persona_description": p.persona_description} for p in personas]
        }

    async def get_by_id(self, persona_id: int, user_id: int) -> Optional[Persona]:
        return await persona_dao.get_by_id_and_user(self.db, persona_id, user_id)

    async def update(self, persona_id: int, user_id: int, persona_name: Optional[str], persona_description: Optional[str]) -> dict:
        if persona_name and len(persona_name) > 288:
            return {"success": False, "code": 20010, "message": "人设名称不能超过288个字符"}
        if persona_description and len(persona_description) > 5000:
            return {"success": False, "code": 20011, "message": "人设描述不能超过5000个字符"}

        persona = await persona_dao.get_by_id_and_user(self.db, persona_id, user_id)
        if not persona:
            return {"success": False, "code": 20012, "message": "人设不存在"}

        update_data = {}
        if persona_name is not None:
            update_data["persona_name"] = persona_name
        if persona_description is not None:
            update_data["persona_description"] = persona_description

        result = await persona_dao.update(self.db, persona_id, user_id, **update_data)
        if not result:
            return {"success": False, "code": 20013, "message": "更新人设失败"}

        return {"success": True, "code": 0, "message": "更新成功", "data": {"persona_id": result.id}}

    async def delete(self, persona_id: int, user_id: int) -> dict:
        persona = await persona_dao.get_by_id_and_user(self.db, persona_id, user_id)
        if not persona:
            return {"success": False, "code": 20020, "message": "人设不存在"}

        result = await persona_dao.delete(self.db, persona_id, user_id)
        if not result:
            return {"success": False, "code": 20021, "message": "删除失败"}

        return {"success": True, "code": 0, "message": "删除成功"}