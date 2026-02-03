"""
雪球爬虫服务 - Xueqiu Crawler
根据 DESIGN_NEWS.md 设计文档创建
包含动态 Token 管理功能
"""
import logging
import requests
import time
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timezone
from urllib.parse import urlencode
import json

logger = logging.getLogger(__name__)


class XueqiuTokenManager:
    """雪球 Token 管理器 - 负责维护 xq_a_token"""

    def __init__(self, redis_client=None):
        self.redis_key = "xueqiu:xq_a_token"
        self.redis_client = redis_client
        self.fallback_token = ""  # 备用 Token
        self.token_ttl = 3600  # Token 默认有效期（秒）

    def get_token(self) -> str:
        """获取 Token"""
        # 优先从 Redis 获取
        if self.redis_client:
            try:
                token = self.redis_client.get(self.redis_key)
                if token:
                    return token.decode('utf-8') if isinstance(token, bytes) else token
            except Exception as e:
                logger.warning(f"从 Redis 获取 Token 失败: {e}")

        # 使用备用 Token
        if self.fallback_token:
            return self.fallback_token

        return ""

    def set_token(self, token: str) -> bool:
        """设置 Token"""
        try:
            self.fallback_token = token
            if self.redis_client:
                self.redis_client.setex(self.redis_key, self.token_ttl, token)
            logger.info("雪球 Token 更新成功")
            return True
        except Exception as e:
            logger.error(f"设置 Token 失败: {e}")
            return False

    def refresh_token(self) -> bool:
        """刷新 Token - 通过访问首页获取"""
        try:
            # 访问雪球首页获取新 Token
            response = requests.get(
                "https://xueqiu.com",
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                },
                timeout=10
            )

            # 从 Cookie 中提取 xq_a_token
            cookies = response.cookies.get_dict()
            token = cookies.get('xq_a_token')

            if token:
                return self.set_token(token)
            else:
                logger.warning("从 Cookie 中未找到 xq_a_token")
                return False

        except Exception as e:
            logger.error(f"刷新 Token 失败: {e}")
            return False


class XueqiuCrawler:
    """雪球爬虫"""

    def __init__(self, redis_client=None):
        self.base_url = "https://xueqiu.com"
        self.token_manager = XueqiuTokenManager(redis_client)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://xueqiu.com/',
        }
        self.timeout = 10
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get_session_with_token(self) -> requests.Session:
        """获取带 Token 的 Session"""
        token = self.token_manager.get_token()
        if token:
            self.session.headers.update({'Cookie': f'xq_a_token={token}'})
        return self.session

    def get_with_retry(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """带重试的GET请求"""
        session = self._get_session_with_token()

        for attempt in range(max_retries):
            try:
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {url}, 错误: {e}")
                if attempt < max_retries - 1:
                    # 尝试刷新 Token
                    if self.token_manager.refresh_token():
                        session = self._get_session_with_token()
                    backoff = 2 ** attempt
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

    def fetch_flash_news(self, limit: int = 50) -> List[Dict]:
        """
        抓取雪球 7x24 快讯

        Args:
            limit: 抓取数量

        Returns:
            新闻列表
        """
        try:
            # 雪球 7x24 快讯 API
            api_url = f"{self.base_url}/statuses/liveroom_v2.json"
            params = {
                'since_id': '-1',
                'max_id': '-1',
                'count': str(limit),
            }

            response = self.get_with_retry(api_url + '?' + urlencode(params))
            if not response:
                return []

            data = response.json()

            if data.get('code') != 0:
                logger.error(f"雪球 API 返回错误: {data.get('error_description', 'Unknown error')}")
                return []

            statuses = data.get('data', {}).get('statuses', [])
            news_list = []

            for item in statuses:
                try:
                    # 使用雪球的 status_id 作为 external_id
                    external_id = item.get('id', '')

                    # 提取内容（可能是纯文本或 HTML）
                    content = item.get('description', '') or item.get('text', '')

                    news_item = {
                        'source': 'xueqiu',
                        'external_id': external_id,
                        'title': '',  # 快讯通常没有标题
                        'content': content,
                        'raw_json': json.dumps(item, ensure_ascii=False),
                        'publish_time': self._parse_timestamp(item.get('created_at', 0)),
                    }
                    news_list.append(news_item)

                except Exception as e:
                    logger.debug(f"解析雪球快讯项失败: {e}")
                    continue

            logger.info(f"雪球抓取成功: {len(news_list)} 条")
            return news_list

        except Exception as e:
            logger.error(f"雪球抓取失败: {e}")
            return []

    def _parse_timestamp(self, timestamp: int) -> datetime:
        """解析时间戳"""
        try:
            if timestamp > 10000000000:  # 毫秒级时间戳
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception as e:
            logger.warning(f"解析时间戳失败: {timestamp}, 错误: {e}")
            return datetime.now(timezone.utc)

    def refresh_token(self) -> bool:
        """刷新 Token"""
        return self.token_manager.refresh_token()


# 单例实例
_xueqiu_crawler = None


def get_xueqiu_crawler(redis_client=None) -> XueqiuCrawler:
    """获取雪球爬虫单例"""
    global _xueqiu_crawler
    if _xueqiu_crawler is None:
        _xueqiu_crawler = XueqiuCrawler(redis_client)
    return _xueqiu_crawler


def get_xueqiu_token_manager(redis_client=None) -> XueqiuTokenManager:
    """获取雪球 Token 管理器单例"""
    return XueqiuTokenManager(redis_client)
