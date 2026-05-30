from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI PR Review Assistant"
    VERSION: str = "1.0.0"

    # GitHub 配置
    GITHUB_TOKEN: Optional[str] = None

    # OpenAI/大模型配置 (提前占位)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # 从根目录的 .env 文件加载环境变量
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# 实例化全局配置对象
settings = Settings()