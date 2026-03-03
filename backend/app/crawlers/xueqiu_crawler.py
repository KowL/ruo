"""
雪球爬虫服务 - Xueqiu Crawler
根据 DESIGN_NEWS.md 设计文档创建
包含动态 Token 管理功能 (Refactored to use AgentBrowser)
"""
import logging
import json
import time
from typing import List, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class XueqiuCrawler:
    """雪球爬虫 - 优先使用 AgentBrowser (Playwright)，失败时使用 requests 备选"""

    def __init__(self, headless: bool = True):
        self.base_url = "https://xueqiu.com"
        self.browser = None
        self._headless = headless
        self._initialized = False
        self._use_requests = False  # 是否使用备选方案

    def _ensure_initialized(self):
        """确保浏览器已初始化并访问过首页 (获取 Cookie)"""
        if self._initialized:
            return
            
        # 尝试使用 Playwright
        try:
            from app.core.agent_browser import AgentBrowser
            self.browser = AgentBrowser(headless=self._headless)
            logger.info("初始化雪球爬虫，访问首页...")
            self.browser.start()
            self.browser.goto(self.base_url)
            # 等待页面加载完成 (networkidle 通常意味着加载完毕)
            # 增加超时时间到 15秒
            self.browser.page.wait_for_load_state('networkidle', timeout=15000)
            logger.info(f"雪球首页访问成功: {self.browser.page.title()}")
            self._initialized = True
        except ImportError as e:
            logger.warning(f"Playwright 不可用，将使用 requests 备选: {e}")
            self._use_requests = True
            self._initialized = True
        except Exception as e:
            logger.warning(f"浏览器初始化失败，将使用 requests 备选: {e}")
            self._use_requests = True
            self._initialized = True

    def _fetch_with_browser(self, url: str) -> Optional[Dict]:
        """使用浏览器 fetch API 请求数据"""
        if not self.browser or not self.browser._page:
            return None
            
        result = self.browser.page.evaluate(f"""
            async () => {{
                try {{
                    const response = await fetch('{url}', {{
                        headers: {{
                            'Referer': '{self.base_url}',
                            'X-Requested-With': 'XMLHttpRequest'
                        }}
                    }});
                    
                    if (!response.ok) {{
                        const text = await response.text();
                        return {{ error: true, status: response.status, text: text }};
                    }}
                    
                    return await response.json();
                }} catch (e) {{
                    return {{ error: true, status: 0, text: e.toString() }};
                }}
            }}
        """)
        
        if isinstance(result, dict) and result.get('error'):
            logger.error(f"API 请求失败: Status {result.get('status')}, Error: {result.get('text')}")
            return None
            
        return result
        
    def _fetch_with_requests(self, url: str) -> Optional[Dict]:
        """使用 requests 请求数据"""
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        try:
            # 先访问首页获取 Cookie
            session = requests.Session()
            session.get(self.base_url, headers=headers, timeout=10)
            
            # 然后请求 API
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Requests 请求失败: {e}")
            return None

    def fetch_hot_posts(self, limit: int = 20) -> List[Dict]:
        """
        抓取雪球今日热门帖子

        Args:
            limit: 抓取数量

        Returns:
            帖子列表
        """
        self._ensure_initialized()
        
        try:
            # 雪球热门帖子 API (Updated to V3)
            api_url = f"{self.base_url}/statuses/hot/listV3.json"
            params = {
                'since_id': '-1',
                'max_id': '-1',
                'size': str(limit),
                'type': 'status',
                'category': '-1',
            }
            
            # 构建带参数的 URL
            from urllib.parse import urlencode
            full_url = f"{api_url}?{urlencode(params)}"
            
            # 根据模式选择请求方式
            if self._use_requests:
                logger.info(f"使用 requests 请求 API (V3): {full_url}")
                data = self._fetch_with_requests(full_url)
            else:
                logger.info(f"在浏览器上下文中请求 API (V3): {full_url}")
                data = self._fetch_with_browser(full_url)
            
            if not data:
                return []
            
            # API 可能会返回 items 列表
            items = data.get('items', [])
            if not items and 'data' in data:
                 items = data['data']
            if not items and 'list' in data:
                 items = data['list']

            if not items:
                logger.warning(f"未找到贴子列表，响应 keys: {list(data.keys())}")
                if 'items' in data:
                    logger.warning(f"items 类型: {type(data['items'])}, 长度: {len(data['items'])}")
                 
            news_list = []

            for item in items:
                try:
                    # 原始贴子数据可能在 original_status 中 (如果是转发)
                    # 但热门帖子通常是直接的主贴
                    status = item.get('original_status', item)
                    
                    external_id = str(status.get('id', ''))
                    
                    # 提取标题和内容
                    title = status.get('title', '')
                    content = status.get('text', '') or status.get('description', '')
                    
                    # 如果没有标题，尝试从内容截取
                    if not title and content:
                        # 移除HTML标签后截取
                        import re
                        clean_text = re.sub(r'<[^>]+>', '', content)
                        title = clean_text[:30] + '...' if len(clean_text) > 30 else clean_text

                    news_item = {
                        'source': 'xueqiu',
                        'external_id': external_id,
                        'title': title,
                        'content': content,
                        'raw_json': json.dumps(item, ensure_ascii=False),
                        'publish_time': self._parse_timestamp(status.get('created_at', 0)),
                        'author': status.get('user', {}).get('screen_name', 'Unknown'),
                        'url': f"https://xueqiu.com{status.get('target', '')}"
                    }
                    news_list.append(news_item)

                except Exception as e:
                    logger.debug(f"解析雪球热贴项失败: {e}")
                    continue

            logger.info(f"雪球热贴抓取成功: {len(news_list)} 条")
            return news_list

        except Exception as e:
            logger.error(f"雪球热贴抓取失败: {e}")
            return []
        finally:
            # 可以在这里选择是否关闭浏览器，或者保持单例常驻
            # 考虑到主要是在 Task 中运行，任务结束后进程可能销毁，或者我们希望保持 Session
            # 暂时不主动关闭，交给析构或外部控制
            pass

    def _parse_timestamp(self, timestamp: int) -> datetime:
        """解析时间戳"""
        try:
            if timestamp > 10000000000:  # 毫秒级时间戳
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception as e:
            logger.warning(f"解析时间戳失败: {timestamp}, 错误: {e}")
            return datetime.now(timezone.utc)
            
    def close(self):
        """关闭资源"""
        if self.browser:
            self.browser.close()


# 单例实例
_xueqiu_crawler = None


def get_xueqiu_crawler(redis_client=None) -> XueqiuCrawler:
    """获取雪球爬虫单例"""
    global _xueqiu_crawler
    if _xueqiu_crawler is None:
        # 在 Docker/服务器环境中通常使用 headless=True
        _xueqiu_crawler = XueqiuCrawler(headless=True)
    return _xueqiu_crawler

# 废弃 TokenManager
class XueqiuTokenManager:
    """
    [DEPRECATED] 雪球 Token 管理器
    不再需要，保留类防止报错
    """
    def __init__(self, redis_client=None):
        pass
        
    def refresh_token(self) -> bool:
        return True
        
    def get_token(self) -> str:
        return "mock_token"

def get_xueqiu_token_manager(redis_client=None) -> XueqiuTokenManager:
    """
    [DEPRECATED] 获取雪球 Token 管理器
    不再需要，保留接口防止报错
    """
    return XueqiuTokenManager(redis_client)
