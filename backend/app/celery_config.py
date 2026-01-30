"""
Celery 配置文件 - Celery Configuration
"""
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

# 创建 Celery 实例
celery_app = Celery(
    'ruo',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
    include=['app.tasks.news_task']
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

    # 任务路由
    task_routes={
        'app.tasks.news_task.fetch_all_stocks_news': {'queue': 'news_queue'},
        'app.tasks.news_task.analyze_unanalyzed_news': {'queue': 'analysis_queue'},
    },

    # 任务默认参数
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',

    # 定时任务
    beat_schedule={
        # 每小时抓取一次新闻
        'fetch-news-hourly': {
            'task': 'app.tasks.news_task.fetch_all_stocks_news',
            'schedule': crontab(minute=0),  # 每小时的整点执行
            'options': {
                'expires': 3600,  # 任务过期时间（秒）
            }
        },
        # 每 30 分钟分析一次未分析的新闻
        'analyze-news-half-hourly': {
            'task': 'app.tasks.news_task.analyze_unanalyzed_news',
            'schedule': crontab(minute='*/30'),  # 每 30 分钟执行
            'options': {
                'expires': 1800,
            }
        },
        # 每天 9:30 抓取早间新闻
        'fetch-morning-news': {
            'task': 'app.tasks.news_task.fetch_all_stocks_news',
            'schedule': crontab(hour=9, minute=30),  # 每天 9:30
            'options': {
                'expires': 3600,
            }
        },
        # 每天 16:30 抓取晚间新闻
        'fetch-evening-news': {
            'task': 'app.tasks.news_task.fetch_all_stocks_news',
            'schedule': crontab(hour=16, minute=30),  # 每天 16:30
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

    # 任务重试
    task_annotations = {
        'tasks.news_task.fetch_all_stocks_news': {
            'rate_limit': '10/h',  # 限制每小时最多 10 次
            'retry_kwargs': {
                'max_retries': 3,
                'countdown': 60,  # 1分钟重试间隔
            },
        },
        'tasks.news_task.analyze_unanalyzed_news': {
            'rate_limit': '20/h',  # 限制每小时最多 20 次
            'retry_kwargs': {
                'max_retries': 2,
                'countdown': 300,  # 5分钟重试间隔
            },
        },
    },
)

# 关闭日志警告
logging.getLogger('celery').setLevel(logging.INFO)

@celery_app.task(bind=True, name='app.tasks.news_task.fetch_all_stocks_news')
def fetch_all_stocks_news(self):
    """
    抓取所有持仓股票的新闻

    任务说明：
    - 从数据库获取所有用户的持仓股票
    - 对每只股票抓取最新的新闻
    - 保存到数据库
    - 如果失败会自动重试
    """
    try:
        from app.services.news import get_news_service
        from app.services.portfolio import get_portfolio_service

        logger.info("开始执行定时任务：抓取所有持仓股票新闻")

        # 获取持仓服务
        portfolio_service = get_portfolio_service()
        news_service = get_news_service()

        # 获取所有持仓股票（过滤活跃的）
        portfolios = portfolio_service.get_portfolio_list(user_id=1, is_active=True)

        if not portfolios:
            logger.info("没有找到活跃的持仓股票，跳过新闻抓取")
            return {'status': 'skipped', 'message': 'No active portfolios'}

        # 收集所有股票代码
        symbols = list(set([p.symbol for p in portfolios if p.symbol]))
        logger.info(f"开始抓取 {len(symbols)} 只股票的新闻")

        # 批量抓取新闻
        results = []
        for symbol in symbols:
            try:
                news_list = news_service.fetch_stock_news(symbol)
                if news_list:
                    saved_count = news_service.save_news(news_list)
                    results.append({
                        'symbol': symbol,
                        'fetched_count': len(news_list),
                        'saved_count': saved_count
                    })
                    logger.info(f"{symbol}: 抓取 {len(news_list)} 条新闻，保存 {saved_count} 条")
                else:
                    logger.debug(f"{symbol}: 没有新新闻")
                    results.append({'symbol': symbol, 'fetched_count': 0, 'saved_count': 0})

            except Exception as e:
                logger.error(f"抓取 {symbol} 新闻失败: {e}")
                results.append({
                    'symbol': symbol,
                    'error': str(e),
                    'fetched_count': 0,
                    'saved_count': 0
                })
                # 继续处理下一个股票
                continue

        summary = {
            'total_symbols': len(symbols),
            'processed_symbols': len(results),
            'fetched_total': sum(r.get('fetched_count', 0) for r in results),
            'saved_total': sum(r.get('saved_count', 0) for r in results),
            'errors': len([r for r in results if 'error' in r]),
            'results': results
        }

        logger.info(f"定时任务完成：抓取股票新闻 - 总共 {summary['total_symbols']} 只股票")
        return summary

    except Exception as e:
        logger.error(f"定时任务失败：抓取股票新闻 - {e}")
        # 自动重试
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, name='app.tasks.news_task.analyze_unanalyzed_news')
def analyze_unanalyzed_news(self):
    """
    分析未分析的新闻

    任务说明：
    - 查询未经过 AI 分析的新闻
    - 批量调用 AI 分析服务
    - 更新分析结果
    - 失败会自动重试
    """
    try:
        from app.services.news import get_news_service
        from app.services.ai_analysis import get_ai_analysis_service

        logger.info("开始执行定时任务：分析未分析的新闻")

        news_service = get_news_service()
        ai_service = get_ai_analysis_service()

        # 获取最近 24 小时内未分析的新闻
        unanalyzed_news = news_service.get_unanalyzed_news(hours=24, limit=20)

        if not unanalyzed_news:
            logger.info("没有需要分析的新闻，跳过")
            return {'status': 'skipped', 'message': 'No news to analyze'}

        logger.info(f"开始分析 {len(unanalyzed_news)} 条未分析的新闻")

        # 批量分析新闻
        results = []
        analyzed_count = 0

        for news in unanalyzed_news:
            try:
                # 分析新闻
                analysis_result = ai_service.analyze_news(news)

                if analysis_result:
                    # 保存分析结果
                    news_service.save_news_analysis(news.id, analysis_result)
                    analyzed_count += 1
                    results.append({
                        'news_id': news.id,
                        'title': news.title[:50] + '...' if len(news.title) > 50 else news.title,
                        'status': 'success',
                        'sentiment': analysis_result.get('sentiment_label', 'unknown')
                    })
                    logger.info(f"分析完成: {news.title[:50]}...")
                else:
                    results.append({
                        'news_id': news.id,
                        'title': news.title[:50] + '...' if len(news.title) > 50 else news.title,
                        'status': 'failed',
                        'error': 'AI analysis returned empty'
                    })

            except Exception as e:
                logger.error(f"分析新闻失败 (ID: {news.id}): {e}")
                results.append({
                    'news_id': news.id,
                    'title': news.title[:50] + '...' if len(news.title) > 50 else news.title,
                    'status': 'failed',
                    'error': str(e)
                })
                # 继续分析下一条
                continue

        summary = {
            'total_news': len(unanalyzed_news),
            'analyzed_count': analyzed_count,
            'failed_count': len([r for r in results if r['status'] == 'failed']),
            'results': results
        }

        logger.info(f"定时任务完成：分析新闻 - 成功 {analyzed_count}/{len(unanalyzed_news)}")
        return summary

    except Exception as e:
        logger.error(f"定时任务失败：分析新闻 - {e}")
        # 自动重试
        raise self.retry(exc=e, countdown=300, max_retries=2)


@celery_app.task(name='app.tasks.news_task.cleanup_old_data')
def cleanup_old_data():
    """
    清理旧数据任务

    每天凌晨执行：
    - 清理 30 天前的新闻
    - 清理缓存
    - 统计数据
    """
    try:
        from app.services.news import get_news_service
        from app.services.market_data import get_market_data_service
        import datetime

        logger.info("开始执行定时任务：清理旧数据")

        news_service = get_news_service()
        market_service = get_market_data_service()

        # 计算 30 天前的日期
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=30)

        # 清理旧新闻
        deleted_count = news_service.delete_old_news(cutoff_date)
        logger.info(f"清理了 {deleted_count} 条旧新闻")

        # 清理缓存
        keys_to_delete = []
        for key in list(market_service.cache.keys()):
            if 'kline:' in key or 'intraday:' in key or 'orderbook:' in key:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del market_service.cache[key]

        logger.info(f"清理了 {len(keys_to_delete)} 条历史缓存")

        # 生成统计报告
        stats = {
            'timestamp': datetime.datetime.now().isoformat(),
            'deleted_news': deleted_count,
            'cleaned_cache_keys': len(keys_to_delete),
            'remaining_cache_size': len(market_service.cache)
        }

        logger.info("定时任务完成：清理旧数据")
        return stats

    except Exception as e:
        logger.error(f"定时任务失败：清理旧数据 - {e}")
        raise