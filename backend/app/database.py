"""数据库引擎与会话 —— 数字化能碳管理系统
本地开发可用 localhost；Docker 内 backend 服务通过主机名 db 访问数据库。
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/energy_carbon",
)

# pool_pre_ping 自动检测失效连接，适配 PostgreSQL 空闲断开
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的声明基类。"""


def get_db():
    """FastAPI 依赖：每次请求提供一个数据库会话，结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
