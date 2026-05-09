from pydantic import BaseModel
from typing import Generic, TypeVar, Optional


T = TypeVar("T")


class CommonResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: str | None = None


class ListResponse(BaseModel, Generic[T]):
    success: bool = True
    list: list[T]
    total: int = 0
