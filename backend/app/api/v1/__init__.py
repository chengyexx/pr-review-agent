from fastapi import APIRouter
from . import pr, auth

api_router = APIRouter()
api_router.include_router(pr.router, prefix="/pr", tags=["Pull Requests"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# 暴露打包好的路由器
__all__ = ["api_router"]