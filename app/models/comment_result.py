from sqlalchemy import Column, Integer, String, Text, SmallInteger
from app.database import Base
from app.models.base import TimestampMixin


class CommentResult(Base, TimestampMixin):
    __tablename__ = "comment_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="所属用户ID")
    post_id = Column(Integer, nullable=False, index=True, comment="关联帖子ID")
    persona_id = Column(Integer, nullable=True, comment="使用的人设ID(可为空)")
    content = Column(Text, nullable=False, comment="生成的评论内容")
    translation = Column(Text, nullable=True, comment="中文翻译")
    suggestion = Column(String(200), nullable=True, comment="使用建议(如语气调整提示)")
    status = Column(String(20), nullable=False, server_default="unused", comment="状态: unused/used")
