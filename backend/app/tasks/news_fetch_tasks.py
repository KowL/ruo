"""
新闻抓取任务 - News Fetch Tasks
根据 DESIGN_NEWS.md 设计文档创建

包含:
- 财联社实时任务 (每60秒触发)
- 雪球快讯任务 (每120秒触发)
- Cookie 刷新任务 (每1小时触发)
"""
import logging
from typing import Dict
from datetime import datetime, timezone
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='app.tasks.news_fetch_tasks.fetch_cls_news_task')
def fetch_cls_news_task(limit: int = 50) -> Dict:
    """
    财联社实时新闻抓取任务

    根据设计文档，每 60 秒触发一次，侧重时效性

    Args:
        limit: 抓取数量

    Returns:
        抓取结果统计
    """
    try:
        from app.crawlers import get_cls_crawler
        from app.services.news_cleaner import get_news_cleaner
        from app.core.database import get_db

        logger.info(f"[财联社] 开始抓取新闻 (数量: {limit})")

        # 1. 抓取财联社电报
        crawler = get_cls_crawler()
        raw_news_list = crawler.fetch_telegraph(limit)

        if not raw_news_list:
            logger.info("[财联社] 没有新新闻")
            return {
                'source': 'cls',
                'fetched': 0,
                'saved': 0,
                'status': 'no_new_data'
            }

        # 2. 数据清洗和去重
        db = next(get_db())
        cleaner = get_news_cleaner(db)

        # 硬去重 (source + external_id)
        deduplicated_list = cleaner.deduplicate_by_source_and_id(raw_news_list)

        # 软去重 (内容哈希)
        deduplicated_list = cleaner.deduplicate_by_content_hash(deduplicated_list)

        # 3. 保存到数据库
        save_result = cleaner.save_to_database(deduplicated_list)

        db.close()

        logger.info(f"[财联社] 抓取完成: 原始 {len(raw_news_list)} 条, "
                   f"去重后 {len(deduplicated_list)} 条, 保存 {save_result['saved']} 条")

        return {
            'source': 'cls',
            'fetched': len(raw_news_list),
            'after_dedup': len(deduplicated_list),
            'saved': save_result['saved'],
            'status': 'success',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"[财联社] 抓取任务失败: {e}")
        return {
            'source': 'cls',
            'fetched': 0,
            'saved': 0,
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='app.tasks.news_fetch_tasks.fetch_xueqiu_news_task')
def fetch_xueqiu_news_task(limit: int = 50) -> Dict:
    """
    雪球快讯抓取任务

    根据设计文档，每 120 秒触发一次，侧重社区和综合快讯

    Args:
        limit: 抓取数量

    Returns:
        抓取结果统计
    """
    try:
        from app.crawlers import get_xueqiu_crawler
        from app.services.news_cleaner import get_news_cleaner
        from app.core.database import get_db
        import redis

        logger.info(f"[雪球] 开始抓取新闻 (数量: {limit})")

        # 1. 获取 Redis 连接（用于 Token 管理）
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        except Exception as e:
            logger.warning(f"[雪球] Redis 连接失败，将使用本地 Token: {e}")
            redis_client = None

        # 2. 抓取雪球快讯
        crawler = get_xueqiu_crawler(redis_client)
        raw_news_list = crawler.fetch_flash_news(limit)

        if not raw_news_list:
            logger.info("[雪球] 没有新新闻")
            return {
                'source': 'xueqiu',
                'fetched': 0,
                'saved': 0,
                'status': 'no_new_data'
            }

        # 3. 数据清洗和去重
        db = next(get_db())
        cleaner = get_news_cleaner(db)

        # 硬去重 (source + external_id)
        deduplicated_list = cleaner.deduplicate_by_source_and_id(raw_news_list)

        # 软去重 (内容哈希)
        deduplicated_list = cleaner.deduplicate_by_content_hash(deduplicated_list)

        # 4. 保存到数据库
        save_result = cleaner.save_to_database(deduplicated_list)

        db.close()

        logger.info(f"[雪球] 抓取完成: 原始 {len(raw_news_list)} 条, "
                   f"去重后 {len(deduplicated_list)} 条, 保存 {save_result['saved']} 条")

        return {
            'source': 'xueqiu',
            'fetched': len(raw_news_list),
            'after_dedup': len(deduplicated_list),
            'saved': save_result['saved'],
            'status': 'success',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"[雪球] 抓取任务失败: {e}")
        return {
            'source': 'xueqiu',
            'fetched': 0,
            'saved': 0,
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='app.tasks.news_fetch_tasks.refresh_xueqiu_token_task')
def refresh_xueqiu_token_task() -> Dict:
    """
    雪球 Token 刷新任务

    根据设计文档，每 1 小时触发一次
    模拟登录雪球以更新抓取所需的 Token

    Returns:
        刷新结果
    """
    try:
        from app.crawlers import get_xueqiu_token_manager
        import redis

        logger.info("[雪球Token] 开始刷新 Token")

        # 获取 Redis 连接
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        except Exception as e:
            logger.warning(f"[雪球Token] Redis 连接失败: {e}")
            redis_client = None

        # 刷新 Token
        token_manager = get_xueqiu_token_manager(redis_client)
        success = token_manager.refresh_token()

        if success:
            logger.info("[雪球Token] Token 刷新成功")
            return {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error("[雪球Token] Token 刷新失败")
            return {
                'status': 'failed',
                'error': 'Failed to refresh token',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    except Exception as e:
        logger.error(f"[雪球Token] 刷新任务失败: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


@shared_task(name='app.tasks.news_fetch_tasks.batch_fetch_news_task')
def batch_fetch_news_task() -> Dict:
    """
    批量新闻抓取任务（聚合所有数据源）

    一次性抓取所有数据源的新闻

    Returns:
        批量抓取结果统计
    """
    logger.info("[批量抓取] 开始批量抓取所有数据源")

    results = {}

    # 财联社
    cls_result = fetch_cls_news_task(limit=50)
    results['cls'] = cls_result

    # 雪球
    xueqiu_result = fetch_xueqiu_news_task(limit=50)
    results['xueqiu'] = xueqiu_result

    # 统计
    total_fetched = sum(r.get('fetched', 0) for r in results.values())
    total_saved = sum(r.get('saved', 0) for r in results.values())

    logger.info(f"[批量抓取] 完成: 财联社 {results['cls'].get('saved', 0)} 条, "
               f"雪球 {results['xueqiu'].get('saved', 0)} 条")

    return {
        'status': 'completed',
        'total_fetched': total_fetched,
        'total_saved': total_saved,
        'details': results,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
