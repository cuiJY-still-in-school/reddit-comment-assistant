from sqlalchemy import Column, Integer, String, Text, SmallInteger
from app.database.connection import Base
from app.database.base import TimestampMixin


class PostRecord(Base, TimestampMixin):
    __tablename__ = "post_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="所属用户ID")
    permalink = Column(String(500), nullable=True, unique=True, comment="帖子永久链接(用于去重)")
    post_title = Column(Text, nullable=True, comment="帖子标题")
    post_content = Column(Text, nullable=False, comment="帖子正文内容")
