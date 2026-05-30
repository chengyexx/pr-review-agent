# 用户认证/登录
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    用户登录接口（支持标准 OAuth2 表单格式）。
    你可以用 admin / admin123 来换取 Token。
    """
    if form_data.username == "admin" and form_data.password == "admin123":
        return {
            "access_token": "mock-secret-token",
            "token_type": "bearer"
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/me")
async def get_me(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    测试获取当前用户信息的接口。
    前端需要在请求头携带 Authorization: Bearer mock-secret-token
    """
    return {"user": current_user}