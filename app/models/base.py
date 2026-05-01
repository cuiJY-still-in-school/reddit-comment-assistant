from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, SmallInteger, func
from app.database import Base


class TimestampMixin:
    create_user = Column(String(100), nullable=True, comment="创建人")
    update_user = Column(String(100), nullable=True, comment="更新人")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    delete_flag = Column(SmallInteger, nullable=False, server_default="0", comment="删除标记 0=未删 1=已删")
