from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.services.reddit_scraper import reddit_scraper
from app.services.style_learner import StyleLearner
from app.schemas.style import StyleSampleRequest, RedditPostResponse
from app.core.response import Response
from app.middleware.auth_middleware import get_current_user_id


router = APIRouter(prefix="/api/style", tags=["风格学习"])


@router.get("/posts")
async def get_reddit_posts(
    subreddit: str = Query(..., description="Subreddit name without r/"),
    sort: str = Query("hot", description="Sort by: hot, new, top"),
    limit: int = Query(10, ge=1, le=25),
):
    posts = await reddit_scraper.get_posts(subreddit, sort, limit)
    return Response.success(
        data={"list": [RedditPostResponse(**p).model_dump() for p in posts], "total": len(posts)},
        message="success",
        code=0
    )


@router.post("/sample")
async def add_style_sample(
    req: StyleSampleRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    learner = StyleLearner(db)
    result = await learner.add_sample(
        user_id=user_id,
        post_title=req.post_title,
        post_content=req.post_content,
        post_url=req.post_url,
        user_comment=req.user_comment,
    )

    if not result["success"]:
        return Response.error(message=result["message"], code=result.get("code", 400))

    return Response.success(data=result["data"], message=result["message"], code=result.get("code", 0))


@router.get("/profile")
async def get_style_profile(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    learner = StyleLearner(db)
    profile = await learner.get_user_profile(user_id)

    if not profile:
        return Response.success(
            data={"profile": None, "sample_count": 0},
            message="No profile yet. Submit samples to build your style profile.",
            code=0
        )

    return Response.success(data={"profile": profile}, message="Profile found", code=0)


@router.post("/analyze")
async def analyze_style(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    learner = StyleLearner(db)
    result = await learner.analyze_user_style(user_id)

    if not result.get("success", False):
        return Response.error(message=result.get("message", "分析失败"), code=result.get("code", 400))

    return Response.success(data=result.get("data", {}), message=result.get("message", "分析完成"), code=result.get("code", 0))


@router.get("/samples")
async def get_style_samples(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    learner = StyleLearner(db)
    offset = (page - 1) * limit
    samples = await learner.get_user_samples(user_id, limit, offset)

    sample_list = [
        {
            "id": s.id,
            "post_title": s.post_title,
            "post_content": (s.post_content[:200] + "...") if s.post_content and len(s.post_content) > 200 else s.post_content,
            "post_url": s.post_url,
            "user_comment": s.user_comment,
            "created_at": s.create_time.isoformat() if s.create_time else None,
        }
        for s in samples
    ]

    return Response.success(data={"list": sample_list, "total": len(sample_list)}, message="success", code=0)


@router.get("/subreddits")
async def get_popular_subreddits():
    subreddits = await reddit_scraper.get_popular_subreddits()
    return Response.success(data={"list": subreddits, "total": len(subreddits)}, message="success", code=0)