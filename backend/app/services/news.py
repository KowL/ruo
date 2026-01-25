"""
新闻服务 - News Service
MVP v0.1

功能：
- F-05: 资讯定时抓取
- 抓取股票新闻
- 存储到数据库
"""
import akshare as ak
from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.news import StockNews

logger = logging.getLogger(__name__)


class NewsService:
    """新闻服务类"""

    def __init__(self, db: Session):
        self.db = db

    def fetch_stock_news(
        self,
        symbol: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        抓取股票新闻 (MVP v0.1 - 使用多种数据源)

        Args:
            symbol: 股票代码
            limit: 抓取数量

        Returns:
            新闻列表
        """
        try:
            # 方法1: 尝试使用东方财富个股新闻 (主要方法)
            try:
                print("1111")
                news_df = ak.stock_news_em(symbol=symbol)
                print(news_df)
                if news_df is not None and not news_df.empty:
                    logger.info(f"成功从东方财富获取新闻: {symbol}, 数量: {len(news_df)}")
                    return self._parse_em_news(news_df, symbol, limit)
            except Exception as e:
                logger.warning(f"东方财富新闻接口失败: {e}")

            # 方法2: 尝试个股资金流
            try:
                news_df = ak.stock_individual_info_em(symbol=symbol)
                if news_df is not None and not news_df.empty:
                    logger.info(f"使用东方财富个股信息: {symbol}")
                    return self._parse_individual_info(news_df, symbol, limit)
            except Exception as e:
                logger.warning(f"个股信息接口失败: {e}")

            # 所有新闻接口均失败
            logger.error(f"所有新闻接口均失败: {symbol}")
            return []

        except Exception as e:
            logger.error(f"抓取股票新闻失败: {symbol}, 错误: {e}")
            return []

    def _parse_em_news(self, news_df, symbol: str, limit: int) -> List[Dict]:
        """解析东方财富新闻数据"""
        news_df = news_df.head(limit)
        news_list = []

        for _, row in news_df.iterrows():
            news_item = {
                'stock_code': symbol,
                'title': row.get('新闻标题', row.get('标题', '无标题')),
                'raw_content': row.get('新闻内容', row.get('摘要', row.get('内容', ''))),
                'source': row.get('信息来源', '东方财富网'),
                'url': row.get('新闻链接', row.get('链接', '')),
                'publish_time': self._parse_publish_time(row.get('发布时间', datetime.now()))
            }
            news_list.append(news_item)

        logger.info(f"成功解析东方财富新闻: {symbol}, 数量: {len(news_list)}")
        return news_list

    def _parse_individual_info(self, news_df, symbol: str, limit: int) -> List[Dict]:
        """解析个股信息数据"""
        news_list = []

        # 从个股信息中提取关键数据作为新闻
        if not news_df.empty:
            info_text = ""
            for _, row in news_df.iterrows():
                item_name = row.get('item', row.get('项目', ''))
                item_value = row.get('value', row.get('数值', ''))
                if item_name and item_value:
                    info_text += f"{item_name}: {item_value}; "

            news_item = {
                'stock_code': symbol,
                'title': f'{symbol} 最新个股信息',
                'raw_content': info_text or '个股基本信息数据',
                'source': '东方财富网',
                'url': '',
                'publish_time': datetime.now()
            }
            news_list.append(news_item)

        logger.info(f"成功解析个股信息: {symbol}")
        return news_list

    def save_news(self, news_list: List[Dict]) -> int:
        """
        保存新闻到数据库

        Args:
            news_list: 新闻列表

        Returns:
            保存成功的数量
        """
        saved_count = 0

        try:
            for news_data in news_list:
                # 检查是否已存在（根据标题和股票代码）
                existing = self.db.query(StockNews).filter(
                    StockNews.stock_code == news_data['stock_code'],
                    StockNews.title == news_data['title']
                ).first()

                if existing:
                    logger.debug(f"新闻已存在，跳过: {news_data['title']}")
                    continue

                # 创建新闻记录
                news = StockNews(
                    stock_code=news_data['stock_code'],
                    title=news_data['title'],
                    raw_content=news_data['raw_content'],
                    source=news_data['source'],
                    url=news_data['url'],
                    publish_time=news_data['publish_time']
                )

                self.db.add(news)
                saved_count += 1

            self.db.commit()
            logger.info(f"成功保存新闻: {saved_count} 条")
            return saved_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存新闻失败: {e}")
            return saved_count

    def get_latest_news(
        self,
        symbol: str,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取最新新闻

        Args:
            symbol: 股票代码
            hours: 最近 N 小时内的新闻
            limit: 返回数量

        Returns:
            新闻列表（包含 AI 分析结果）
        """
        try:
            # 计算时间范围
            start_time = datetime.now() - timedelta(hours=hours)

            # 查询新闻
            news_query = self.db.query(StockNews).filter(
                StockNews.stock_code == symbol,
                StockNews.publish_time >= start_time
            ).order_by(StockNews.publish_time.desc()).limit(limit)

            news_list = news_query.all()

            # 转换为字典
            result = []
            for news in news_list:
                news_dict = {
                    'id': news.id,
                    'stock_code': news.stock_code,
                    'title': news.title,
                    'raw_content': news.raw_content,
                    'source': news.source,
                    'url': news.url,
                    'publish_time': news.publish_time.strftime('%Y-%m-%d %H:%M:%S') if news.publish_time else None,
                    'created_at': news.created_at.strftime('%Y-%m-%d %H:%M:%S') if news.created_at else None
                }
                result.append(news_dict)

            return result

        except Exception as e:
            logger.error(f"获取最新新闻失败: {symbol}, 错误: {e}")
            return []

    def get_news_with_analysis(
        self,
        symbol: str,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取新闻及 AI 分析结果

        Args:
            symbol: 股票代码
            hours: 最近 N 小时内的新闻
            limit: 返回数量

        Returns:
            新闻列表（包含 AI 分析）
        """
        try:
            from app.models.news import NewsAnalysis

            # 计算时间范围
            start_time = datetime.now() - timedelta(hours=hours)

            # 联表查询
            query = self.db.query(StockNews, NewsAnalysis).outerjoin(
                NewsAnalysis, StockNews.id == NewsAnalysis.news_id
            ).filter(
                StockNews.stock_code == symbol,
                StockNews.publish_time >= start_time
            ).order_by(StockNews.publish_time.desc()).limit(limit)

            results = query.all()

            # 转换为字典
            news_with_analysis = []
            for news, analysis in results:
                news_dict = {
                    'id': news.id,
                    'title': news.title,
                    'raw_content': news.raw_content,
                    'source': news.source,
                    'url': news.url,
                    'publish_time': news.publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                }

                # 添加 AI 分析结果
                if analysis:
                    news_dict['ai_summary'] = analysis.ai_summary
                    news_dict['sentiment_label'] = analysis.sentiment_label
                    news_dict['sentiment_score'] = analysis.sentiment_score
                    news_dict['llm_model'] = analysis.llm_model
                else:
                    news_dict['ai_summary'] = None
                    news_dict['sentiment_label'] = None
                    news_dict['sentiment_score'] = None

                news_with_analysis.append(news_dict)

            return news_with_analysis

        except Exception as e:
            logger.error(f"获取新闻及分析失败: {symbol}, 错误: {e}")
            return []

    def fetch_and_save_news(self, symbol: str, limit: int = 10) -> Dict:
        """
        抓取并保存新闻（一步完成）

        Args:
            symbol: 股票代码
            limit: 抓取数量

        Returns:
            {
                "fetched": 抓取数量,
                "saved": 保存数量
            }
        """
        # 1. 抓取新闻
        news_list = self.fetch_stock_news(symbol, limit)

        # 2. 保存到数据库
        saved_count = self.save_news(news_list)

        return {
            "fetched": len(news_list),
            "saved": saved_count
        }

    def _parse_publish_time(self, time_str) -> datetime:
        """
        解析发布时间

        Args:
            time_str: 时间字符串或 datetime 对象

        Returns:
            datetime 对象
        """
        if isinstance(time_str, datetime):
            return time_str

        try:
            # 尝试解析常见格式
            if isinstance(time_str, str):
                # 格式1: 2024-01-22 10:30:00
                if len(time_str) == 19:
                    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                # 格式2: 2024-01-22
                elif len(time_str) == 10:
                    return datetime.strptime(time_str, '%Y-%m-%d')
                # 格式3: 01-22 10:30
                elif '-' in time_str and ':' in time_str:
                    current_year = datetime.now().year
                    return datetime.strptime(f"{current_year}-{time_str}", '%Y-%m-%d %H:%M')

            # 无法解析，返回当前时间
            return datetime.now()

        except Exception as e:
            logger.warning(f"解析时间失败: {time_str}, 错误: {e}")
            return datetime.now()
