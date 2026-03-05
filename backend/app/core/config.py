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
    PROJECT_NAME: str = "Ruo.ai"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "ruo_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "ruo_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ruo")

    @property
    def DATABASE_URL(self) -> str:
        """动态生成数据库连接 URL"""
        # 优先使用环境变量中的 DATABASE_URL
        env_db_url = os.getenv("DATABASE_URL")
        if env_db_url:
            return env_db_url
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_DB}"

    # Redis 配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # LLM 配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")

    # 特定厂商配置 (保持向下兼容)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

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
    USE_TUSHARE: bool = True
    TUSHARE_TOKEN: str = os.getenv("TUSHARE_TOKEN", "")

    # Celery 配置
    @property
    def CELERY_BROKER_URL(self) -> str:
        """从 Redis 配置生成 Broker URL"""
        env_url = os.getenv("CELERY_BROKER_URL")
        if env_url:
            return env_url
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """从 Redis 配置生成 Result Backend URL"""
        env_url = os.getenv("CELERY_RESULT_BACKEND")
        if env_url:
            return env_url
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

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
