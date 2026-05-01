from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.comment_service import CommentService
from app.schemas.comment import (
    GenerateCommentRequest, GenerateCommentResponse, CommentResponse,
    MarkUsedRequest, MarkUsedResponse,
)
from app.utils.rate_limiter import get_rate_limiter
from app.config import settings
from app.middleware.auth_middleware import get_current_user_id
from datetime import datetime


router = APIRouter(prefix="/api/comment", tags=["评论生成"])


@router.post("/generate", response_model=GenerateCommentResponse)
async def generate_comment(
    req: GenerateCommentRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    limiter = get_rate_limiter()
    allowed = await limiter.is_allowed(f"user:{user_id}", settings.rate_limit_per_minute)
    if not allowed:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后重试")

    service = CommentService(db)
    result = await service.generate(user_id, req.post_content, req.permalink, req.persona_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("message", "生成失败"))

    return GenerateCommentResponse(
        list=[CommentResponse(**c) for c in result["comments"]],
        persona_name=result.get("persona_name"),
        generate_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )


@router.post("/use", response_model=MarkUsedResponse)
async def mark_comment_used(
    req: MarkUsedRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    service = CommentService(db)
    result = await service.mark_used(user_id, req.comment_id)
    return MarkUsedResponse(success=result["success"])
