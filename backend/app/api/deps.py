# 依赖注入 (如获取 DB 实例、当前用户)
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

# 使用 OAuth2 密码流机制，指定前端去哪个接口获取 Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    解析 Token 并获取当前用户的依赖项。
    在实际项目中，这里会解析 JWT Token 并查库。
    为了不阻碍初期开发，我们提供一个坚固的 Mock 验证机制。
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Mock 校验逻辑
    if token == "mock-secret-token":
        return {"username": "admin", "role": "developer"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的 Token 或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )