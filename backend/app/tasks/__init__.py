"""
Celery 任务入口文件 - Celery Tasks Entry Point
"""
from .celery_config import celery_app

__all__ = ('celery_app',)