from pydantic import BaseModel


class CommonResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: str | None = None


class ListResponse(BaseModel):
    success: bool = True
    list: list
    total: int = 0
