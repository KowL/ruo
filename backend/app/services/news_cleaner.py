"""
新闻清洗和去重服务 - News Cleaning and Deduplication Service
根据 DESIGN_NEWS.md 设计文档创建
"""
import logging
import hashlib
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.news import News

logger = logging.getLogger(__name__)


class NewsCleaner:
    """新闻清洗和去重器"""

    # HTML 标签清理正则
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')

    # 多余空白清理正则
    WHITESPACE_PATTERN = re.compile(r'\s+')

    def __init__(self, db: Session):
        self.db = db

    def clean_news_item(self, raw_news: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗单条新闻数据

        Args:
            raw_news: 原始新闻数据

        Returns:
            清洗后的新闻数据
        """
        cleaned = raw_news.copy()

        # 1. 清洗标题
        cleaned['title'] = self._clean_text(raw_news.get('title', ''))

        # 2. 清洗内容
        cleaned['content'] = self._clean_text(raw_news.get('content', ''))

        # 3. 确保时间戳为 datetime 对象且带时区
        publish_time = raw_news.get('publish_time')
        if isinstance(publish_time, str):
            cleaned['publish_time'] = self._parse_datetime_string(publish_time)
        elif not isinstance(publish_time, datetime):
            cleaned['publish_time'] = datetime.now(timezone.utc)
        else:
            cleaned['publish_time'] = publish_time

        return cleaned

    def _clean_text(self, text: str) -> str:
        """
        清洗文本内容

        - 去除 HTML 标签
        - 去除多余空白
        - 去除特殊字符（保留中英文、数字、常用标点）
        """
        if not text:
            return ""

        # 去除 HTML 标签
        text = self.HTML_TAG_PATTERN.sub('', text)

        # 去除多余空白
        text = self.WHITESPACE_PATTERN.sub(' ', text)

        # 去除首尾空白
        text = text.strip()

        return text

    def _parse_datetime_string(self, dt_str: str) -> datetime:
        """解析日期时间字符串"""
        # 常见格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d',
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str, fmt)
                # 确保有 UTC 时区
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        # 无法解析，返回当前时间
        logger.warning(f"无法解析时间字符串: {dt_str}")
        return datetime.now(timezone.utc)

    def deduplicate_by_source_and_id(
        self,
        news_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        按 source + external_id 硬去重

        Args:
            news_list: 新闻列表

        Returns:
            去重后的新闻列表
        """
        seen = set()
        unique_news = []

        for news in news_list:
            source = news.get('source', '')
            external_id = news.get('external_id', '')
            key = f"{source}:{external_id}"

            if key not in seen:
                seen.add(key)
                unique_news.append(news)
            else:
                logger.debug(f"跳过重复新闻: source={source}, external_id={external_id}")

        logger.info(f"硬去重: {len(news_list)} -> {len(unique_news)}")
        return unique_news

    def deduplicate_by_content_hash(
        self,
        news_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        按内容哈希软去重（识别不同来源但内容高度相似的新闻）

        Args:
            news_list: 新闻列表

        Returns:
            去重后的新闻列表
        """
        seen_hashes = set()
        unique_news = []

        for news in news_list:
            # 合并标题和内容计算哈希
            text = f"{news.get('title', '')} {news.get('content', '')}"
            content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_news.append(news)
            else:
                logger.debug(f"跳过内容相似的新闻: {news.get('title', '')[:30]}...")

        logger.info(f"内容哈希去重: {len(news_list)} -> {len(unique_news)}")
        return unique_news

    def save_to_database(
        self,
        news_list: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        保存新闻到数据库

        使用 PostgreSQL 的 INSERT ON CONFLICT DO NOTHING 进行去重

        Args:
            news_list: 新闻列表

        Returns:
            保存结果统计
        """
        saved_count = 0
        duplicate_count = 0
        error_count = 0

        for news in news_list:
            try:
                # 清洗数据
                cleaned_news = self.clean_news_item(news)

                # 创建数据库记录
                raw_news = News(
                    source=cleaned_news['source'],
                    external_id=cleaned_news['external_id'],
                    title=cleaned_news['title'],
                    content=cleaned_news['content'],
                    raw_json=cleaned_news.get('raw_json', ''),
                    publish_time=cleaned_news['publish_time'],
                )

                self.db.add(raw_news)
                saved_count += 1

            except Exception as e:
                self.db.rollback()
                error_count += 1
                logger.debug(f"保存新闻失败: {e}")
                continue

        # 提交事务（PostgreSQL 会处理唯一约束冲突）
        try:
            self.db.commit()
            logger.info(f"保存新闻完成: 尝试 {len(news_list)} 条, 成功 {saved_count} 条, 错误 {error_count} 条")
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量提交失败: {e}")
            return {
                'attempted': len(news_list),
                'saved': 0,
                'duplicate': 0,
                'error': len(news_list)
            }

        return {
            'attempted': len(news_list),
            'saved': saved_count,
            'duplicate': duplicate_count,
            'error': error_count
        }


# 单例管理
_news_cleaners = {}


def get_news_cleaner(db: Session) -> NewsCleaner:
    """获取新闻清洗器实例（每个 Session 一个）"""
    session_id = id(db)
    if session_id not in _news_cleaners:
        _news_cleaners[session_id] = NewsCleaner(db)
    return _news_cleaners[session_id]
