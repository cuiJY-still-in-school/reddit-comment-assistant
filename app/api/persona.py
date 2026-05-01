from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.persona_service import PersonaService
from app.schemas.persona import (
    PersonaCreateRequest, PersonaUpdateRequest,
    PersonaResponse, PersonaListResponse,
)
from app.schemas.common import CommonResponse
from app.middleware.auth_middleware import get_current_user_id


router = APIRouter(prefix="/api/persona", tags=["人设管理"])


@router.post("/create", response_model=CommonResponse)
async def create_persona(
    req: PersonaCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    service = PersonaService(db)
    result = await service.create(user_id, req.persona_name, req.persona_description)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    persona = result["persona"]
    return CommonResponse(
        success=True,
        message="创建成功",
        data={
            "persona_id": persona.id,
            "persona_name": persona.persona_name,
            "persona_description": persona.persona_description,
            "create_time": str(persona.create_time),
        },
    )


@router.get("/list", response_model=PersonaListResponse)
async def list_personas(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    service = PersonaService(db)
    personas = await service.list(user_id)
    return PersonaListResponse(
        list=[
            PersonaResponse(
                id=p.id,
                persona_name=p.persona_name,
                persona_description=p.persona_description,
                create_time=str(p.create_time),
            )
            for p in personas
        ],
        total=len(personas),
    )


@router.put("/update", response_model=CommonResponse)
async def update_persona(
    req: PersonaUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    service = PersonaService(db)
    result = await service.update(req.persona_id, user_id, req.persona_name, req.persona_description)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    persona = result["persona"]
    return CommonResponse(
        success=True,
        message="修改成功",
        data={
            "persona_id": persona.id,
            "persona_name": persona.persona_name,
            "persona_description": persona.persona_description,
        },
    )


@router.delete("/delete", response_model=CommonResponse)
async def delete_persona(
    persona_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    service = PersonaService(db)
    result = await service.delete(persona_id, user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return CommonResponse(success=True, message=result["message"])
