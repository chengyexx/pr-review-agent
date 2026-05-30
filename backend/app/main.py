# FastAPI 入口文件
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 直接从 v1 模块引入打包好的 api_router
from app.api.v1 import api_router

app = FastAPI(
    title="AI PR Review Assistant API",
    description="七牛云笔试题目三后端接口",
    version="1.0.0"
)

# 配置跨域（方便前端本地联调）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境请修改为具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 V1 版本的所有路由，并统一加上 /api/v1 前缀
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to AI PR Review Assistant API"}
