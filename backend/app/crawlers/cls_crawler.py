"""
财联社爬虫服务 - Cailian Press Crawler
根据 DESIGN_NEWS.md 设计文档创建
"""
import logging
import requests
import time
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ClsCrawler:
    """财联社爬虫"""

    def __init__(self):
        self.base_url = "https://www.cls.cn"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.cls.cn/telegraph',
        }
        self.timeout = 10
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_with_retry(self, url: str, max_retries: int = 3, **kwargs) -> Optional[requests.Response]:
        """带重试的GET请求"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {url}, 错误: {e}")
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt  # 指数退避
                    time.sleep(backoff)
                else:
                    logger.error(f"请求最终失败: {url}")
                    return None
            except Exception as e:
                logger.warning(f"请求异常 (尝试 {attempt + 1}/{max_retries}): {url}, 错误: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None

    def fetch_telegraph(self, limit: int = 50) -> List[Dict]:
        """
        抓取财联社电报快讯

        Args:
            limit: 抓取数量

        Returns:
            新闻列表
        """
        try:
            # 财联社电报 API
            api_url = f"{self.base_url}/nodeapi/telegraphList"
            params = {
                'os': 'web',
                'rn': limit,
                'sub': 'telegraph',
                'type': 'telegraph',
                'token': '',
            }

            response = self.get_with_retry(api_url, params=params)
            if not response:
                return []

            data = response.json()

            # 新 API 使用 error 字段，0 表示成功
            if data.get('error') != 0:
                logger.error(f"财联社 API 返回错误: {data.get('msg', 'Unknown error')}")
                return []

            # 新 API 数据在 data.roll_data 中
            telegraph_list = data.get('data', {}).get('roll_data', [])
            news_list = []

            for item in telegraph_list:
                try:
                    # 新 API 有 id 字段，可以直接使用
                    external_id = str(item.get('id', ''))
                    if not external_id:
                        # 如果没有 id，使用内容 hash 作为 external_id
                        external_id = self._generate_content_hash(
                            item.get('content', '') + str(item.get('ctime', 0))
                        )

                    news_item = {
                        'source': 'cls',
                        'external_id': external_id,
                        'title': item.get('title', '') or item.get('brief', ''),  # 优先使用 title
                        'content': item.get('content', ''),
                        'raw_json': str(item),  # 存储原始数据
                        'publish_time': self._parse_timestamp(item.get('ctime', 0)),  # 使用 ctime
                    }
                    news_list.append(news_item)

                except Exception as e:
                    logger.debug(f"解析财联社电报项失败: {e}")
                    continue

            logger.info(f"财联社抓取成功: {len(news_list)} 条")
            return news_list

        except Exception as e:
            logger.error(f"财联社抓取失败: {e}")
            return []

    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希值，用于唯一标识"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _parse_timestamp(self, timestamp: int) -> datetime:
        """解析时间戳"""
        try:
            if timestamp > 10000000000:  # 毫秒级时间戳
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception as e:
            logger.warning(f"解析时间戳失败: {timestamp}, 错误: {e}")
            return datetime.now(timezone.utc)


# 单例实例
_cls_crawler = None


def get_cls_crawler() -> ClsCrawler:
    """获取财联社爬虫单例"""
    global _cls_crawler
    if _cls_crawler is None:
        _cls_crawler = ClsCrawler()
    return _cls_crawler
