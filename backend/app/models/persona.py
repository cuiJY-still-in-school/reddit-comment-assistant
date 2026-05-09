from sqlalchemy import Column, Integer, String, Text
from app.database.connection import Base
from app.database.base import TimestampMixin


class Persona(Base, TimestampMixin):
    __tablename__ = "persona"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="所属用户ID")
    persona_name = Column(String(288), nullable=True, comment="人设名称")
    persona_description = Column(Text, nullable=True, comment="人设描述(风格/语气/角色设定)")
