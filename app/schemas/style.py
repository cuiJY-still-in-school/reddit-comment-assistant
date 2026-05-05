from pydantic import BaseModel, Field
from typing import Optional


class StyleSampleRequest(BaseModel):
    post_id: Optional[str] = None
    post_title: str = ""
    post_content: str = ""
    post_url: str = ""
    user_comment: str = Field(..., min_length=1)


class StyleProfileResponse(BaseModel):
    sample_count: int = 0
    avg_length: Optional[int] = None
    avg_word_count: Optional[int] = None
    common_words: list[str] = []
    tone_patterns: list[str] = []
    formality_score: float = 0.5
    humor_score: float = 0.3
    aggression_score: float = 0.2
    emoji_usage_rate: float = 0.0
    sentence_style: dict = {}
    updated_at: Optional[str] = None


class RedditPostResponse(BaseModel):
    id: str
    title: str
    content: str
    url: str
    score: int
    num_comments: int
    subreddit: str
    author: str = ""