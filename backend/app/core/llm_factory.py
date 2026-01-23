"""
LLM 工厂模块

统一管理和创建 LLM 实例，避免重复初始化
"""

import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def create_llm(model: str = "deepseek-v3-1-terminus", **kwargs):
    """
    创建 LLM 实例

    Args:
        model: 模型名称，默认为 deepseek-v3-1-terminus
        **kwargs: 其他 LLM 参数

    Returns:
        ChatOpenAI 实例
    """
    default_config = {
        "model": model,
        "openai_api_base": "https://ark.cn-beijing.volces.com/api/v3",
        "openai_api_key": os.getenv("ARK_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "temperature": 0.6,
    }

    # 合并用户提供的配置
    config = {**default_config, **kwargs}

    return ChatOpenAI(**config)


def get_shared_llm():
    """
    获取共享的 LLM 实例（单例模式）

    Returns:
        ChatOpenAI 实例
    """
    if not hasattr(get_shared_llm, '_instance'):
        get_shared_llm._instance = create_llm()

    return get_shared_llm._instance


def reset_shared_llm():
    """重置共享的 LLM 实例"""
    if hasattr(get_shared_llm, '_instance'):
        delattr(get_shared_llm, '_instance')


class LLMFactory:
    """LLM 工厂类，提供单例模式的 LLM 实例管理"""

    _instance = None

    @classmethod
    def get_instance(cls):
        """获取 LLM 实例（单例模式）"""
        if cls._instance is None:
            cls._instance = get_shared_llm()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置 LLM 实例"""
        cls._instance = None
        reset_shared_llm()

    @classmethod
    def create_new_instance(cls, model: str = "deepseek-v3-1-terminus", **kwargs):
        """创建新的 LLM 实例"""
        return create_llm(model, **kwargs)