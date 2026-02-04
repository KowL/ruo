"""
Celery 配置文件 - Celery Configuration
根据 DESIGN_NEWS.md 设计文档更新
"""
from celery import Celery
from celery.schedules import crontab
import logging
import os

logger = logging.getLogger(__name__)

# 从环境变量获取配置
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

# 创建 Celery 实例
celery_app = Celery(
    'ruo',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.news_fetch_tasks',  # 新闻抓取任务
        'app.tasks.price_tasks',       # 价格更新任务
        'app.tasks.stock_tasks',       # 股票同步任务
    ]
)

# Celery 配置
celery_app.conf.update(
    # 时区设置
    timezone='Asia/Shanghai',
    enable_utc=True,

    # 任务序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # 任务默认参数
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',

    # 定时任务 - 根据 DESIGN_NEWS.md 设计
    beat_schedule={
        # === 股票同步任务 ===
        'sync-stocks-daily': {
            'task': 'app.tasks.stock_tasks.sync_stocks_task',
            'schedule': crontab(hour=0, minute=0),  # 每天凌晨 0:00
            'options': {
                'expires': 3600,
            }
        },

        # === 价格更新任务 ===
        'update-portfolio-prices-every-20s': {
            'task': 'app.tasks.price_tasks.update_portfolio_prices_task',
            'schedule': 10.0,  # 每 10 秒 (交易时间内执行)
            'options': {
                'expires': 60,
            }
        },

        # === 新闻抓取任务 ===

        # 财联社实时任务：每 60 秒触发一次（侧重时效性）
        'fetch-cls-news-every-minute': {
            'task': 'app.tasks.news_fetch_tasks.fetch_cls_news_task',
            'schedule': 60.0,  # 每 60 秒
            'options': {
                'expires': 120,  # 任务过期时间（秒）
            }
        },

        # 雪球快讯任务：每 120 秒触发一次（侧重社区和综合快讯）
        'fetch-xueqiu-news-every-2-minutes': {
            'task': 'app.tasks.news_fetch_tasks.fetch_xueqiu_news_task',
            'schedule': 120.0,  # 每 120 秒
            'options': {
                'expires': 180,
            }
        },

        # Cookie 刷新任务：每 1 小时触发一次
        'refresh-xueqiu-token-hourly': {
            'task': 'app.tasks.news_fetch_tasks.refresh_xueqiu_token_task',
            'schedule': crontab(minute=0),  # 每小时的整点执行
            'options': {
                'expires': 300,
            }
        },

        # 每天凌晨清理旧数据
        'cleanup-old-data-daily': {
            'task': 'app.tasks.news_fetch_tasks.batch_fetch_news_task',
            'schedule': crontab(hour=2, minute=0),  # 凌晨 2:00
            'options': {
                'expires': 3600,
            }
        },
    },

    # 任务执行
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,

    # 日志配置
    worker_log_level='INFO',
    task_log_level='INFO',

    # 结果过期
    result_expires=3600,  # 1小时后过期

    # 任务重试配置
    task_annotations={
        # 价格更新任务
        'app.tasks.price_tasks.update_portfolio_prices_task': {
            'rate_limit': '50/m',
        },
        # 新闻抓取任务重试配置
        'app.tasks.news_fetch_tasks.fetch_cls_news_task': {
            'autoretry_for': (Exception,),
            'retry_kwargs': {
                'max_retries': 3,
                'countdown': 30,  # 30秒重试间隔
            },
            'rate_limit': '20/m',  # 每分钟最多 20 次
        },
        'app.tasks.news_fetch_tasks.fetch_xueqiu_news_task': {
            'autoretry_for': (Exception,),
            'retry_kwargs': {
                'max_retries': 3,
                'countdown': 30,
            },
            'rate_limit': '20/m',
        },
        'app.tasks.news_fetch_tasks.refresh_xueqiu_token_task': {
            'autoretry_for': (Exception,),
            'retry_kwargs': {
                'max_retries': 2,
                'countdown': 60,  # 1分钟重试间隔
            },
            'rate_limit': '2/m',  # 每分钟最多 2 次
        },
    },
)

# 关闭日志警告
logging.getLogger('celery').setLevel(logging.INFO)
