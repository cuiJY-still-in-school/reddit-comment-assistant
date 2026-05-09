from sqlalchemy import Column, Integer, String, DateTime, Text, SmallInteger
from app.database.connection import Base
from app.database.base import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True, comment="用户名")
    email = Column(String(200), nullable=False, unique=True, comment="邮箱")
    password_hash = Column(String(255), nullable=True, comment="密码哈希(bcrypt)")
    auth_method = Column(String(20), nullable=False, server_default="password", comment="认证方式: password")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    login_fail_count = Column(Integer, nullable=False, server_default="0", comment="连续登录失败次数")
    locked_until = Column(DateTime, nullable=True, comment="锁定截止时间")
    status = Column(SmallInteger, nullable=False, server_default="1", comment="状态: 1=正常 0=禁用")
