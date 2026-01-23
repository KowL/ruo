"""
应用配置
Application Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""

    # 基础配置
    PROJECT_NAME: str = "Ruo - AI 智能投顾副驾"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "ruo"
    POSTGRES_PASSWORD: str = "123456"
    POSTGRES_DB: str = "ruo"

    @property
    def DATABASE_URL(self) -> str:
        """动态生成数据库连接 URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # LLM 配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"

    # 其他 LLM API 配置
    LANGSMITH_PROJECT: str = ""
    DASHSCOPE_API_KEY: str = ""
    ARK_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_ENABLED: str = "false"

    # 数据源配置
    USE_TUSHARE: bool = False
    TUSHARE_TOKEN: str = ""

    # Celery 配置
    CELERY_BROKER_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"
    CELERY_RESULT_BACKEND: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/2"

    # 项目路径
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    CACHE_DIR: Path = BASE_DIR / "cache"
    REPORTS_DIR: Path = BASE_DIR / "reports"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
