from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI PR Review Assistant"
    VERSION: str = "1.0.0"

    # GitHub 配置
    GITHUB_TOKEN: Optional[str] = None

    # 大模型配置
    API_KEY: Optional[str] = None
    BASE_URL: Optional[str] = None
    MODEL: Optional[str] = None

    # 从根目录的 .env 文件加载环境变量
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# 实例化全局配置对象
settings = Settings()