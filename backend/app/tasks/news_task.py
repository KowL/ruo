"""
新闻抓取和分析任务 - News Fetch and Analysis Tasks
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def fetch_stock_news_task(symbol: str, hours: int = 24) -> Dict:
    """
    抓取单只股票的新闻

    Args:
        symbol: 股票代码
        hours: 抓取最近 N 小时的新闻

    Returns:
        抓取结果字典
    """
    try:
        from app.services.news import get_news_service

        logger.info(f"开始抓取 {symbol} 的新闻（最近 {hours} 小时）")

        news_service = get_news_service()
        news_list = news_service.fetch_stock_news(symbol)

        if not news_list:
            return {
                'status': 'success',
                'symbol': symbol,
                'fetched_count': 0,
                'saved_count': 0,
                'message': 'No new news found'
            }

        saved_count = news_service.save_news(news_list)

        logger.info(f"{symbol}: 抓取 {len(news_list)} 条新闻，保存 {saved_count} 条")

        return {
            'status': 'success',
            'symbol': symbol,
            'fetched_count': len(news_list),
            'saved_count': saved_count,
            'message': f'Successfully fetched and saved news'
        }

    except Exception as e:
        logger.error(f"抓取 {symbol} 新闻失败: {e}")
        return {
            'status': 'error',
            'symbol': symbol,
            'error': str(e),
            'fetched_count': 0,
            'saved_count': 0
        }


def analyze_news_task(news_id: int) -> Dict:
    """
    分析单条新闻

    Args:
        news_id: 新闻 ID

    Returns:
        分析结果字典
    """
    try:
        from app.services.news import get_news_service
        from app.services.ai_analysis import get_ai_analysis_service

        logger.info(f"开始分析新闻 (ID: {news_id})")

        news_service = get_news_service()
        ai_service = get_ai_analysis_service()

        # 获取新闻
        news = news_service.get_news_by_id(news_id)
        if not news:
            return {
                'status': 'error',
                'news_id': news_id,
                'error': 'News not found'
            }

        # 分析新闻
        analysis_result = ai_service.analyze_news(news)

        if not analysis_result:
            return {
                'status': 'error',
                'news_id': news_id,
                'error': 'AI analysis returned empty result'
            }

        # 保存分析结果
        news_service.save_news_analysis(news_id, analysis_result)

        logger.info(f"新闻分析完成 (ID: {news_id}): {analysis_result.get('sentiment_label', 'unknown')}")

        return {
            'status': 'success',
            'news_id': news_id,
            'sentiment_label': analysis_result.get('sentiment_label', 'unknown'),
            'sentiment_score': analysis_result.get('sentiment_score', 0),
            'ai_summary': analysis_result.get('ai_summary', '')
        }

    except Exception as e:
        logger.error(f"分析新闻失败 (ID: {news_id}): {e}")
        return {
            'status': 'error',
            'news_id': news_id,
            'error': str(e)
        }


def batch_fetch_news_task(symbols: List[str], hours: int = 24) -> Dict:
    """
    批量抓取多只股票的新闻

    Args:
        symbols: 股票代码列表
        hours: 抓取最近 N 小时的新闻

    Returns:
        批量抓取结果字典
    """
    try:
        logger.info(f"开始批量抓取 {len(symbols)} 只股票的新闻")

        results = []
        for symbol in symbols:
            result = fetch_stock_news_task(symbol, hours)
            results.append(result)

        # 统计结果
        total_fetched = sum(r['fetched_count'] for r in results)
        total_saved = sum(r['saved_count'] for r in results)
        error_count = sum(1 for r in results if r['status'] == 'error')

        logger.info(f"批量抓取完成: {len(symbols)} 只股票, "
                   f"抓取 {total_fetched} 条, 保存 {total_saved} 条, 错误 {error_count} 个")

        return {
            'status': 'success',
            'total_symbols': len(symbols),
            'total_fetched': total_fetched,
            'total_saved': total_saved,
            'error_count': error_count,
            'results': results
        }

    except Exception as e:
        logger.error(f"批量抓取新闻失败: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'total_fetched': 0,
            'total_saved': 0
        }


def batch_analyze_news_task(news_ids: List[int]) -> Dict:
    """
    批量分析多条新闻

    Args:
        news_ids: 新闻 ID 列表

    Returns:
        批量分析结果字典
    """
    try:
        logger.info(f"开始批量分析 {len(news_ids)} 条新闻")

        results = []
        for news_id in news_ids:
            result = analyze_news_task(news_id)
            results.append(result)

        # 统计结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')

        logger.info(f"批量分析完成: {len(news_ids)} 条新闻, "
                   f"成功 {success_count} 条, 失败 {error_count} 条")

        return {
            'status': 'success',
            'total_news': len(news_ids),
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        }

    except Exception as e:
        logger.error(f"批量分析新闻失败: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'total_news': len(news_ids),
            'success_count': 0,
            'error_count': 0
        }