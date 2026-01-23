"""
新闻爬虫服务 - News Crawler Service
MVP v0.1+

功能：
- 爬取雪球网股票新闻
- 爬取同花顺股票新闻
- 爬取东方财富网股票新闻
- 提供统一的新闻数据接口
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import json
import re
import time

logger = logging.getLogger(__name__)


class NewsCrawler:
    """新闻爬虫基类"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        self.timeout = 10
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_with_retry(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """带重试的GET请求"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except Exception as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {url}, 错误: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # 指数退避
                else:
                    logger.error(f"请求最终失败: {url}")
                    return None


class XueqiuCrawler(NewsCrawler):
    """雪球网新闻爬虫"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://xueqiu.com"
        # 雪球需要先访问首页获取cookie
        self._init_session()

    def _init_session(self):
        """初始化会话(获取cookie)"""
        try:
            self.session.get(self.base_url, timeout=self.timeout)
            logger.debug("雪球会话初始化成功")
        except Exception as e:
            logger.warning(f"雪球会话初始化失败: {e}")

    def fetch_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        抓取雪球股票新闻

        Args:
            symbol: 股票代码 如 'SH600519' 或 '600519'
            limit: 抓取数量

        Returns:
            新闻列表
        """
        try:
            # 转换股票代码格式
            if len(symbol) == 6:
                if symbol.startswith('6'):
                    symbol = f'SH{symbol}'
                else:
                    symbol = f'SZ{symbol}'

            # 雪球API端点
            api_url = f"https://xueqiu.com/statuses/search.json"
            params = {
                'count': limit,
                'comment': 0,
                'symbol': symbol,
                'hl': 0,
                'source': 'all',
                'sort': 'time',
                'page': 1,
                'q': '',
                'type': 'status'
            }

            response = self.get_with_retry(api_url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()]))

            if not response:
                return []

            data = response.json()
            news_list = []

            if 'list' in data:
                for item in data['list'][:limit]:
                    news_item = {
                        'title': self._clean_text(item.get('title', item.get('description', '')[:50])),
                        'content': self._clean_text(item.get('description', item.get('text', ''))),
                        'source': '雪球',
                        'url': f"https://xueqiu.com{item.get('target', '')}",
                        'publish_time': self._parse_timestamp(item.get('created_at', 0))
                    }
                    news_list.append(news_item)

            logger.info(f"雪球抓取成功: {symbol}, 数量: {len(news_list)}")
            return news_list

        except Exception as e:
            logger.error(f"雪球抓取失败: {symbol}, 错误: {e}")
            return []

    def _clean_text(self, text: str) -> str:
        """清理文本(去除HTML标签)"""
        if not text:
            return ""
        # 去除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _parse_timestamp(self, timestamp: int) -> datetime:
        """解析时间戳"""
        try:
            if timestamp > 10000000000:  # 毫秒级时间戳
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp)
        except:
            return datetime.now()


class TonghuashunCrawler(NewsCrawler):
    """同花顺新闻爬虫"""

    def fetch_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        抓取同花顺股票新闻

        Args:
            symbol: 股票代码 如 '600519'
            limit: 抓取数量

        Returns:
            新闻列表
        """
        try:
            # 同花顺新闻API
            url = f"http://basic.10jqka.com.cn/{symbol}/news.html"

            response = self.get_with_retry(url)
            if not response:
                return []

            response.encoding = 'gbk'  # 同花顺使用GBK编码
            soup = BeautifulSoup(response.text, 'html.parser')

            news_list = []
            # 查找新闻列表
            news_items = soup.select('.news_list li') or soup.select('.newslist li')

            for item in news_items[:limit]:
                try:
                    # 提取标题和链接
                    title_elem = item.select_one('a') or item.select_one('.title a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url_link = title_elem.get('href', '')
                    if url_link and not url_link.startswith('http'):
                        url_link = f"http://news.10jqka.com.cn{url_link}"

                    # 提取时间
                    time_elem = item.select_one('.time') or item.select_one('span')
                    time_str = time_elem.get_text(strip=True) if time_elem else ''

                    news_item = {
                        'title': title,
                        'content': title,  # 同花顺列表页只有标题
                        'source': '同花顺',
                        'url': url_link,
                        'publish_time': self._parse_time_str(time_str)
                    }
                    news_list.append(news_item)

                except Exception as e:
                    logger.debug(f"解析同花顺新闻项失败: {e}")
                    continue

            logger.info(f"同花顺抓取成功: {symbol}, 数量: {len(news_list)}")
            return news_list

        except Exception as e:
            logger.error(f"同花顺抓取失败: {symbol}, 错误: {e}")
            return []

    def _parse_time_str(self, time_str: str) -> datetime:
        """解析时间字符串"""
        try:
            # 处理各种时间格式
            time_str = time_str.strip()

            # 格式1: "01-23 10:30"
            if re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}', time_str):
                current_year = datetime.now().year
                return datetime.strptime(f"{current_year}-{time_str}", '%Y-%m-%d %H:%M')

            # 格式2: "2026-01-23"
            elif re.match(r'\d{4}-\d{2}-\d{2}', time_str):
                return datetime.strptime(time_str, '%Y-%m-%d')

            # 默认返回当前时间
            return datetime.now()

        except:
            return datetime.now()


class EastmoneyCrawler(NewsCrawler):
    """东方财富网新闻爬虫"""

    def fetch_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        抓取东方财富网股票新闻

        Args:
            symbol: 股票代码 如 '600519'
            limit: 抓取数量

        Returns:
            新闻列表
        """
        try:
            # 东方财富新闻搜索API
            # 构建市场代码
            if symbol.startswith('6'):
                market_code = f'1.{symbol}'  # 上海
            elif symbol.startswith('0') or symbol.startswith('3'):
                market_code = f'0.{symbol}'  # 深圳
            else:
                market_code = f'0.{symbol}'

            # 使用东方财富的新闻接口
            api_url = f"https://search-api-web.eastmoney.com/search/jsonp"
            params = {
                'cb': 'jQuery',
                'param': json.dumps({
                    'uid': '',
                    'keyword': symbol,
                    'type': ['cmsArticleWebOld'],
                    'client': 'web',
                    'clientType': 'web',
                    'clientVersion': 'curr',
                    'param': {
                        'cmsArticleWebOld': {
                            'searchScope': 'default',
                            'sort': 'default',
                            'pageIndex': 1,
                            'pageSize': limit
                        }
                    }
                }),
                '_': str(int(time.time() * 1000))
            }

            response = self.get_with_retry(api_url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()]))

            if not response:
                # 备选方案:直接爬取网页
                return self._fetch_from_web(symbol, limit)

            # 解析JSONP响应
            text = response.text
            # 提取JSON部分
            json_match = re.search(r'jQuery.*?\((.*)\)', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return self._parse_api_response(data, limit)
            else:
                return self._fetch_from_web(symbol, limit)

        except Exception as e:
            logger.error(f"东方财富抓取失败: {symbol}, 错误: {e}")
            return self._fetch_from_web(symbol, limit)

    def _fetch_from_web(self, symbol: str, limit: int) -> List[Dict]:
        """从网页直接抓取"""
        try:
            url = f"https://so.eastmoney.com/news/s?keyword={symbol}"
            response = self.get_with_retry(url)

            if not response:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_list = []

            # 查找新闻列表
            news_items = soup.select('.news-item') or soup.select('.list-box .item')

            for item in news_items[:limit]:
                try:
                    title_elem = item.select_one('.title a') or item.select_one('a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url_link = title_elem.get('href', '')

                    # 提取摘要
                    content_elem = item.select_one('.content') or item.select_one('.desc')
                    content = content_elem.get_text(strip=True) if content_elem else title

                    # 提取时间
                    time_elem = item.select_one('.time') or item.select_one('.date')
                    time_str = time_elem.get_text(strip=True) if time_elem else ''

                    news_item = {
                        'title': title,
                        'content': content,
                        'source': '东方财富网',
                        'url': url_link,
                        'publish_time': self._parse_time_str(time_str)
                    }
                    news_list.append(news_item)

                except Exception as e:
                    logger.debug(f"解析东方财富新闻项失败: {e}")
                    continue

            logger.info(f"东方财富网页抓取成功: {symbol}, 数量: {len(news_list)}")
            return news_list

        except Exception as e:
            logger.error(f"东方财富网页抓取失败: {symbol}, 错误: {e}")
            return []

    def _parse_api_response(self, data: dict, limit: int) -> List[Dict]:
        """解析API响应"""
        news_list = []
        try:
            articles = data.get('result', {}).get('cmsArticleWebOld', [])
            for article in articles[:limit]:
                news_item = {
                    'title': article.get('title', ''),
                    'content': article.get('content', article.get('title', '')),
                    'source': article.get('mediaName', '东方财富网'),
                    'url': article.get('url', ''),
                    'publish_time': self._parse_datetime(article.get('showTime', ''))
                }
                news_list.append(news_item)
        except Exception as e:
            logger.error(f"解析东方财富API响应失败: {e}")

        return news_list

    def _parse_time_str(self, time_str: str) -> datetime:
        """解析时间字符串"""
        try:
            time_str = time_str.strip()

            # 格式: "01-23 10:30" 或 "2026-01-23"
            if re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}', time_str):
                current_year = datetime.now().year
                return datetime.strptime(f"{current_year}-{time_str}", '%Y-%m-%d %H:%M')
            elif re.match(r'\d{4}-\d{2}-\d{2}', time_str):
                return datetime.strptime(time_str[:10], '%Y-%m-%d')

            return datetime.now()
        except:
            return datetime.now()

    def _parse_datetime(self, dt_str: str) -> datetime:
        """解析完整日期时间"""
        try:
            # "2026-01-23 10:30:00"
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except:
            return datetime.now()


class NewsAggregator:
    """新闻聚合器 - 整合多个数据源"""

    def __init__(self):
        self.xueqiu = XueqiuCrawler()
        self.tonghuashun = TonghuashunCrawler()
        self.eastmoney = EastmoneyCrawler()

    def fetch_all(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        从所有数据源抓取新闻并聚合

        Args:
            symbol: 股票代码
            limit: 每个源抓取的数量

        Returns:
            聚合后的新闻列表(去重、按时间排序)
        """
        all_news = []

        # 并发抓取各个数据源
        logger.info(f"开始聚合抓取新闻: {symbol}")

        # 雪球
        try:
            xueqiu_news = self.xueqiu.fetch_news(symbol, limit)
            all_news.extend(xueqiu_news)
            logger.info(f"雪球: {len(xueqiu_news)} 条")
        except Exception as e:
            logger.warning(f"雪球抓取异常: {e}")

        # 同花顺
        try:
            ths_news = self.tonghuashun.fetch_news(symbol, limit)
            all_news.extend(ths_news)
            logger.info(f"同花顺: {len(ths_news)} 条")
        except Exception as e:
            logger.warning(f"同花顺抓取异常: {e}")

        # 东方财富
        try:
            em_news = self.eastmoney.fetch_news(symbol, limit)
            all_news.extend(em_news)
            logger.info(f"东方财富: {len(em_news)} 条")
        except Exception as e:
            logger.warning(f"东方财富抓取异常: {e}")

        # 去重(基于标题相似度)
        unique_news = self._deduplicate(all_news)

        # 按时间排序
        unique_news.sort(key=lambda x: x.get('publish_time', datetime.min), reverse=True)

        # 限制总数量
        result = unique_news[:limit * 2]  # 返回2倍数量以保证质量

        logger.info(f"聚合完成: 原始 {len(all_news)} 条, 去重后 {len(unique_news)} 条, 返回 {len(result)} 条")
        return result

    def _deduplicate(self, news_list: List[Dict]) -> List[Dict]:
        """去重新闻(基于标题)"""
        seen_titles = set()
        unique_news = []

        for news in news_list:
            title = news.get('title', '').strip()
            # 简单去重:标题前30个字符相同视为重复
            title_key = title[:30] if len(title) > 30 else title

            if title_key not in seen_titles and title:
                seen_titles.add(title_key)
                unique_news.append(news)

        return unique_news


# 单例实例
_news_aggregator = None

def get_news_aggregator() -> NewsAggregator:
    """获取新闻聚合器单例"""
    global _news_aggregator
    if _news_aggregator is None:
        _news_aggregator = NewsAggregator()
    return _news_aggregator
