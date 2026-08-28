"""FastAPI 应用入口。启动自动建表 + 写入种子数据。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, carbon, dashboard, energy, system
from .database import engine
from init_db import init_db, seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：建表并灌入默认基础数据（企业信息 / 能源类型 / 碳因子 / 排放源 / admin）
    init_db()
    seed()
    yield


app = FastAPI(
    title="数字化能碳管理系统",
    version="1.0.0",
    description="本地运行的能碳管理系统后端 API",
    lifespan=lifespan,
)

# CORS：允许前端开发端口（5173）与 nginx 部署端口（18080/8080）跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:18080", "http://127.0.0.1:18080",
        "http://localhost:8080", "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 各业务路由已在各自模块内定义 '/api/<模块>' 前缀，
# 与前端 axios baseURL='/api'、vite proxy、nginx 反向代理路径一致
app.include_router(auth.router)
app.include_router(system.router)
app.include_router(energy.router)
app.include_router(carbon.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"name": "数字化能碳管理系统", "version": "1.0.0", "docs": "/docs"}
