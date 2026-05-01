from pydantic import BaseModel, Field
from typing import Optional


class GenerateCommentRequest(BaseModel):
    post_content: str = Field(..., min_length=1)
    permalink: Optional[str] = Field(None, max_length=500)
    persona_id: Optional[int] = None


class CommentResponse(BaseModel):
    comment_id: int
    content: str
    suggestion: Optional[str] = None


class GenerateCommentResponse(BaseModel):
    list: list[CommentResponse]
    persona_name: Optional[str] = None
    generate_time: str


class MarkUsedRequest(BaseModel):
    comment_id: int


class MarkUsedResponse(BaseModel):
    success: bool
