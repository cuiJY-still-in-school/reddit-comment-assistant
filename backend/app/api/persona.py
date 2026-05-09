from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.services.persona_service import PersonaService
from app.schemas.persona import PersonaCreateRequest, PersonaUpdateRequest
from app.core.response import Response
from app.middleware.auth_middleware import get_current_user_id


router = APIRouter(prefix="/api/persona", tags=["人设管理"])


@router.post("/create")
async def create_persona(
    req: PersonaCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    service = PersonaService(db)
    result = await service.create(user_id, req.persona_name, req.persona_description)

    if not result["success"]:
        return Response.error(message=result["message"], code=result.get("code", 400))

    return Response.success(data=result["data"], message=result["message"], code=result.get("code", 0))


@router.get("/list")
async def list_personas(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    service = PersonaService(db)
    result = await service.list(user_id)

    if not result["success"]:
        return Response.error(message=result["message"], code=result.get("code", 400))

    return Response.success(data=result["data"], message=result["message"], code=result.get("code", 0))


@router.put("/update")
async def update_persona(
    req: PersonaUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    service = PersonaService(db)
    result = await service.update(req.persona_id, user_id, req.persona_name, req.persona_description)

    if not result["success"]:
        return Response.error(message=result["message"], code=result.get("code", 400))

    return Response.success(data=result["data"], message=result["message"], code=result.get("code", 0))


@router.delete("/delete")
async def delete_persona(
    persona_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    service = PersonaService(db)
    result = await service.delete(persona_id, user_id)

    if not result["success"]:
        return Response.error(message=result["message"], code=result.get("code", 400))

    return Response.success(message=result["message"], code=result.get("code", 0))