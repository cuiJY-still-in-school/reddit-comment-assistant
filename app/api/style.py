from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.reddit_scraper import reddit_scraper
from app.services.style_learner import StyleLearner
from app.schemas.style import (
    StyleSampleRequest, StyleProfileResponse, RedditPostResponse,
)
from app.schemas.common import CommonResponse, ListResponse
from app.middleware.auth_middleware import get_current_user_id


router = APIRouter(prefix="/api/style", tags=["风格学习"])


@router.get("/posts", response_model=ListResponse[RedditPostResponse])
async def get_reddit_posts(
    subreddit: str = Query(..., description="Subreddit name without r/"),
    sort: str = Query("hot", description="Sort by: hot, new, top"),
    limit: int = Query(10, ge=1, le=25),
    user_id: int = Depends(get_current_user_id),
):
    posts = await reddit_scraper.get_posts(subreddit, sort, limit)
    return ListResponse(
        success=True,
        list=[RedditPostResponse(**p) for p in posts],
        total=len(posts),
    )


@router.post("/sample", response_model=CommonResponse)
async def add_style_sample(
    req: StyleSampleRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    learner = StyleLearner(db)
    sample = await learner.add_sample(
        user_id=user_id,
        post_title=req.post_title,
        post_content=req.post_content,
        post_url=req.post_url,
        user_comment=req.user_comment,
    )
    return CommonResponse(
        success=True,
        message="Sample added",
        data={"sample_id": sample.id, "sample_count": 1},
    )


@router.get("/profile", response_model=CommonResponse)
async def get_style_profile(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    learner = StyleLearner(db)
    profile = await learner.get_user_profile(user_id)

    if not profile:
        return CommonResponse(
            success=True,
            message="No profile yet. Submit samples to build your style profile.",
            data={"profile": None, "sample_count": 0},
        )

    return CommonResponse(
        success=True,
        message="Profile found",
        data={"profile": profile},
    )


@router.post("/analyze", response_model=CommonResponse)
async def analyze_style(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    learner = StyleLearner(db)
    analysis = await learner.analyze_user_style(user_id)

    if not analysis:
        return CommonResponse(
            success=False,
            message="Not enough samples to analyze. Need at least 1 sample.",
            data={},
        )

    return CommonResponse(
        success=True,
        message=f"Analysis complete. Analyzed {analysis.get('sample_count', 0)} samples.",
        data=analysis,
    )


@router.get("/samples", response_model=ListResponse)
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
            "post_content": s.post_content[:200] + "..." if s.post_content and len(s.post_content) > 200 else s.post_content,
            "post_url": s.post_url,
            "user_comment": s.user_comment,
            "created_at": s.create_time.isoformat() if s.create_time else None,
        }
        for s in samples
    ]

    return ListResponse(
        success=True,
        list=sample_list,
        total=len(sample_list),
    )


@router.get("/subreddits", response_model=ListResponse)
async def get_popular_subreddits(
    user_id: int = Depends(get_current_user_id),
):
    subreddits = await reddit_scraper.get_popular_subreddits()
    return ListResponse(
        success=True,
        list=subreddits,
        total=len(subreddits),
    )