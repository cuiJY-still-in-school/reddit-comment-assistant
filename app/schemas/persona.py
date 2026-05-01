from pydantic import BaseModel, Field
from typing import Optional


class PersonaCreateRequest(BaseModel):
    persona_name: Optional[str] = Field(None, max_length=288)
    persona_description: Optional[str] = None


class PersonaUpdateRequest(BaseModel):
    persona_id: int
    persona_name: Optional[str] = Field(None, max_length=288)
    persona_description: Optional[str] = None


class PersonaResponse(BaseModel):
    id: int
    persona_name: Optional[str]
    persona_description: Optional[str]
    create_time: str

    model_config = {"from_attributes": True}


class PersonaListResponse(BaseModel):
    list: list[PersonaResponse]
    total: int
