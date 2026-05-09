from sqlalchemy import Column, Integer, String, Text, DateTime, SmallInteger, Float, func
from sqlalchemy.sql.sqltypes import JSON
from app.database.connection import Base
from app.database.base import TimestampMixin


class StyleSample(Base, TimestampMixin):
    __tablename__ = "style_sample"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    post_title = Column(Text, nullable=True, comment="帖子标题")
    post_content = Column(Text, nullable=True, comment="帖子内容")
    post_url = Column(Text, nullable=True, comment="帖子URL")
    user_comment = Column(Text, nullable=False, comment="用户写的评论")
    upvotes = Column(Integer, default=0, comment="获得的 upvotes")
    analysis_data = Column(JSON, nullable=True, comment="分析数据JSON")


class StyleProfile(Base, TimestampMixin):
    __tablename__ = "style_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, comment="用户ID")
    avg_length = Column(Integer, nullable=True, comment="平均评论长度")
    avg_word_count = Column(Integer, nullable=True, comment="平均词数")
    common_words = Column(JSON, nullable=True, comment="常用词JSON数组")
    tone_patterns = Column(JSON, nullable=True, comment="语气模式JSON数组")
    formality_score = Column(Float, default=0.5, comment="正式程度 0-1")
    humor_score = Column(Float, default=0.5, comment="幽默程度 0-1")
    aggression_score = Column(Float, default=0.5, comment="攻击性 0-1")
    emoji_usage_rate = Column(Float, default=0.0, comment="emoji使用率")
    sentence_style = Column(JSON, nullable=True, comment="句子风格JSON")
    topic_keywords = Column(JSON, nullable=True, comment="话题关键词JSON")
    sample_count = Column(Integer, default=0, comment="样本数量")