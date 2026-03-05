"""
LLM 工厂模块

统一管理和创建 LLM 实例，避免重复初始化
"""

import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from app.core.config import settings


def create_llm(model: str = None, **kwargs):
    """
    创建 LLM 实例

    Args:
        model: 模型名称，默认为 settings.DEFAULT_LLM_MODEL
        **kwargs: 其他 LLM 参数
    """
    actual_model = model or settings.DEFAULT_LLM_MODEL
    
    default_config = {
        "model": actual_model,
        "base_url": settings.LLM_BASE_URL,
        "api_key": settings.LLM_API_KEY,
        "temperature": 0.6,
    }

    # 合并用户提供的配置
    config = {**default_config, **kwargs}

    return ChatOpenAI(**config)


class LLMFactory:
    """LLM 工厂类，提供单例模式的 LLM 实例管理"""

    _instance = None

    @classmethod
    def get_instance(cls):
        """获取 LLM 实例（单例模式）"""
        if cls._instance is None:
            cls._instance = create_llm()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置 LLM 实例"""
        cls._instance = None

    @classmethod
    def create_new_instance(cls, model: str = "deepseek-v3-1-terminus", **kwargs):
        """创建新的 LLM 实例"""
        return create_llm(model, **kwargs)