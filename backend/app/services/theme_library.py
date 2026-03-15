"""
题材库服务 - Theme Library Service
提供题材分类、强度排行、生命周期追踪等功能

功能：
- 从 AKShare 获取概念板块数据
- 涨停股票与题材自动关联
- 题材强度计算与排行
- 题材生命周期追踪（发酵/高潮/退潮）
- 龙头股自动识别
- Redis 缓存支持
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
import redis
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class ThemeData:
    """题材数据结构"""
    theme_name: str
    theme_level: int  # 1=一级题材(大概念), 2=二级题材(细分)
    parent_theme: Optional[str]  # 父题材名称
    hot_score: int  # 热度评分 0-100
    limit_up_count: int  # 涨停股数量
    continuous_days: int  # 持续天数
    leader_stocks: List[Dict]  # 龙头股列表
    follower_stocks: List[Dict]  # 跟风股列表
    lifecycle: str  # 发酵期/高潮期/退潮期
    change_pct: float  # 板块涨跌幅
    turnover: float  # 换手率
    fund_flow: float  # 资金流向（亿元）
    update_time: str


class ThemeLibraryService:
    """题材库服务"""

    _instance = None
    _lock = Lock()

    # 生命周期阶段定义
    LIFECYCLE_FERMENT = "发酵期"
    LIFECYCLE_BOOM = "高潮期"
    LIFECYCLE_DECLINE = "退潮期"

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.cache_ttl = 300  # 缓存 5 分钟
        self.theme_history = {}  # 题材历史数据（用于计算生命周期）

    @classmethod
    def get_instance(cls, redis_client=None) -> 'ThemeLibraryService':
        """单例获取"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(redis_client)
            return cls._instance

    def _get_redis(self):
        """获取 Redis 客户端"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True
                )
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}")
                return None
        return self.redis_client

    def _get_akshare_concept_boards(self) -> pd.DataFrame:
        """
        从 AKShare 获取概念板块列表

        Returns:
            概念板块 DataFrame
        """
        try:
            import akshare as ak
            # 获取东方财富概念板块
            df = ak.stock_board_concept_name_em()
            return df
        except Exception as e:
            logger.error(f"获取概念板块失败: {e}")
            return pd.DataFrame()

    def _get_concept_cons(self, concept_name: str) -> pd.DataFrame:
        """
        获取概念板块成分股

        Args:
            concept_name: 概念名称

        Returns:
            成分股 DataFrame
        """
        try:
            import akshare as ak
            df = ak.stock_board_concept_cons_em(symbol=concept_name)
            return df
        except Exception as e:
            logger.warning(f"获取概念成分股失败 {concept_name}: {e}")
            return pd.DataFrame()

    def _get_limit_up_stocks(self) -> List[Dict]:
        """
        获取今日涨停股票列表

        Returns:
            涨停股票列表
        """
        try:
            import akshare as ak
            df = ak.stock_zt_pool_em()
            if df.empty:
                return []
            
            result = []
            for _, row in df.iterrows():
                # 从涨停原因提取题材
                reason = str(row.get('涨停原因', ''))
                themes = self._extract_themes_from_reason(reason)
                
                result.append({
                    'symbol': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'price': float(row.get('最新价', 0)) if row.get('最新价') else 0,
                    'change_pct': float(row.get('涨跌幅(%)', 0)) if row.get('涨跌幅(%)') else 0,
                    'limit_up_days': self._parse_consecutive_days(reason),
                    'reason': reason,
                    'themes': themes,
                    'first_limit_time': str(row.get('首次封板时间', '')),
                    'last_limit_time': str(row.get('最后封板时间', '')),
                    'turnover': float(row.get('成交额(亿元)', 0)) if row.get('成交额(亿元)') else 0,
                })
            return result
        except Exception as e:
            logger.error(f"获取涨停数据失败: {e}")
            return []

    def _extract_themes_from_reason(self, reason: str) -> List[str]:
        """
        从涨停原因中提取题材

        Args:
            reason: 涨停原因字符串

        Returns:
            题材列表
        """
        themes = []
        # 常见题材关键词映射
        theme_keywords = {
            '人工智能': ['AI', '人工智能', '大模型', 'ChatGPT', 'AIGC', '算力'],
            '机器人': ['机器人', '人形机器人', '工业机器人', '减速器', '伺服电机'],
            '新能源汽车': ['新能源汽车', '电动车', '锂电池', '固态电池', '充电桩'],
            '半导体': ['半导体', '芯片', '光刻机', '封测', 'EDA', '存储芯片'],
            '光伏': ['光伏', '太阳能', '组件', '逆变器', '硅料'],
            '储能': ['储能', '电池储能', '户储', '大储'],
            '医药': ['医药', '创新药', 'CXO', '医疗器械', '中药'],
            '军工': ['军工', '国防', '航空航天', '船舶', '雷达'],
            '金融': ['券商', '银行', '保险', '金融科技', '数字货币'],
            '地产': ['房地产', '地产', '建材', '装修', '家居'],
            '消费': ['消费', '零售', '食品饮料', '白酒', '免税'],
            '文化传媒': ['传媒', '游戏', '影视', '短剧', '元宇宙'],
        }
        
        for theme, keywords in theme_keywords.items():
            for keyword in keywords:
                if keyword in reason:
                    themes.append(theme)
                    break
        
        return themes if themes else ['其他']

    def _parse_consecutive_days(self, reason: str) -> int:
        """
        从涨停原因中解析连板数

        Args:
            reason: 涨停原因

        Returns:
            连板数
        """
        import re
        match = re.search(r'第(\d+)板', reason)
        if match:
            return int(match.group(1))
        return 1

    def _calculate_theme_hot_score(self, limit_up_count: int, continuous_days: int, 
                                   leader_strength: int, fund_flow: float) -> int:
        """
        计算题材热度评分

        Args:
            limit_up_count: 涨停股数量
            continuous_days: 持续天数
            leader_strength: 龙头强度（最高连板数）
            fund_flow: 资金流向

        Returns:
            热度评分 0-100
        """
        # 基础分：涨停数量占比 40分
        score = min(limit_up_count * 2, 40)
        
        # 持续性：持续天数占比 20分
        score += min(continuous_days * 5, 20)
        
        # 龙头强度：最高连板数占比 25分
        score += min(leader_strength * 5, 25)
        
        # 资金流向：占比 15分
        if fund_flow > 10:
            score += 15
        elif fund_flow > 5:
            score += 10
        elif fund_flow > 0:
            score += 5
        
        return min(score, 100)

    def _determine_lifecycle(self, theme_name: str, current_data: Dict) -> str:
        """
        判断题材生命周期阶段

        Args:
            theme_name: 题材名称
            current_data: 当前数据

        Returns:
            生命周期阶段
        """
        # 获取历史数据
        history = self.theme_history.get(theme_name, [])
        if len(history) < 2:
            return self.LIFECYCLE_FERMENT
        
        # 分析趋势
        recent_limit_up = [h.get('limit_up_count', 0) for h in history[-5:]]
        
        # 连续增长 → 发酵期
        if len(recent_limit_up) >= 3 and all(recent_limit_up[i] <= recent_limit_up[i+1] 
                                              for i in range(len(recent_limit_up)-1)):
            return self.LIFECYCLE_FERMENT
        
        # 涨停数峰值后下降 → 退潮期
        if len(recent_limit_up) >= 3:
            max_idx = recent_limit_up.index(max(recent_limit_up))
            if max_idx < len(recent_limit_up) - 1:
                return self.LIFECYCLE_DECLINE
        
        # 涨停数维持高位 → 高潮期
        if current_data.get('limit_up_count', 0) >= 5:
            return self.LIFECYCLE_BOOM
        
        return self.LIFECYCLE_FERMENT

    def _identify_leader_stocks(self, stocks: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        识别龙头股和跟风股

        Args:
            stocks: 股票列表

        Returns:
            (龙头股列表, 跟风股列表)
        """
        if not stocks:
            return [], []
        
        # 按连板数排序
        sorted_stocks = sorted(stocks, key=lambda x: x.get('limit_up_days', 1), reverse=True)
        
        # 最高连板数作为龙头
        max_days = sorted_stocks[0].get('limit_up_days', 1)
        
        leaders = []
        followers = []
        
        for stock in sorted_stocks:
            if stock.get('limit_up_days', 1) == max_days:
                stock['positioning'] = '龙头' if len(leaders) == 0 else '中军'
                leaders.append(stock)
            elif stock.get('limit_up_days', 1) >= max_days - 1:
                stock['positioning'] = '先锋'
                leaders.append(stock)
            else:
                stock['positioning'] = '补涨'
                followers.append(stock)
        
        return leaders, followers

    def get_theme_library(self, min_hot_score: int = 0, limit: int = 50) -> Dict:
        """
        获取题材库数据

        Args:
            min_hot_score: 最小热度评分
            limit: 返回数量限制

        Returns:
            题材库数据
        """
        redis_client = self._get_redis()
        cache_key = f"theme:library:{min_hot_score}:{limit}"

        # 尝试从缓存获取
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info("从 Redis 缓存获取题材库数据")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis 读取失败: {e}")

        try:
            # 获取涨停股票
            limit_up_stocks = self._get_limit_up_stocks()
            
            # 按题材分组统计
            theme_stats = {}
            for stock in limit_up_stocks:
                for theme in stock.get('themes', ['其他']):
                    if theme not in theme_stats:
                        theme_stats[theme] = {
                            'stocks': [],
                            'total_limit_up_days': 0,
                        }
                    theme_stats[theme]['stocks'].append(stock)
                    theme_stats[theme]['total_limit_up_days'] += stock.get('limit_up_days', 1)

            # 构建题材数据
            result = []
            for theme_name, stats in theme_stats.items():
                stocks = stats['stocks']
                limit_up_count = len(stocks)
                
                # 识别龙头股和跟风股
                leaders, followers = self._identify_leader_stocks(stocks)
                max_limit_up_days = leaders[0].get('limit_up_days', 1) if leaders else 1
                
                # 计算持续天数（简化：使用最近有涨停的天数）
                continuous_days = min(5, limit_up_count)  # 简化计算
                
                # 计算热度评分
                hot_score = self._calculate_theme_hot_score(
                    limit_up_count, continuous_days, max_limit_up_days, 0
                )
                
                # 判断生命周期
                lifecycle = self._determine_lifecycle(theme_name, {
                    'limit_up_count': limit_up_count,
                    'continuous_days': continuous_days
                })
                
                # 更新历史数据
                if theme_name not in self.theme_history:
                    self.theme_history[theme_name] = []
                self.theme_history[theme_name].append({
                    'limit_up_count': limit_up_count,
                    'timestamp': datetime.now().isoformat()
                })
                # 只保留最近10条
                self.theme_history[theme_name] = self.theme_history[theme_name][-10:]

                theme_data = ThemeData(
                    theme_name=theme_name,
                    theme_level=2,  # 默认为二级题材
                    parent_theme=None,  # 暂不关联父题材
                    hot_score=hot_score,
                    limit_up_count=limit_up_count,
                    continuous_days=continuous_days,
                    leader_stocks=leaders[:3],  # 只保留前3个龙头
                    follower_stocks=followers[:5],  # 只保留前5个跟风股
                    lifecycle=lifecycle,
                    change_pct=0,  # 需要额外获取板块涨跌幅
                    turnover=0,  # 需要额外计算
                    fund_flow=0,  # 需要额外获取
                    update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                
                # 过滤热度
                if theme_data.hot_score >= min_hot_score:
                    result.append(asdict(theme_data))

            # 按热度排序
            result.sort(key=lambda x: x['hot_score'], reverse=True)
            result = result[:limit]

            response = {
                'status': 'success',
                'data': result,
                'count': len(result),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 写入缓存
            if redis_client:
                try:
                    redis_client.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(response, ensure_ascii=False)
                    )
                except Exception as e:
                    logger.warning(f"Redis 写入失败: {e}")

            return response

        except Exception as e:
            logger.error(f"获取题材库失败: {e}")
            return {
                'status': 'error',
                'data': [],
                'count': 0,
                'message': str(e)
            }

    def get_theme_ranking(self, sort_by: str = 'hot_score', limit: int = 20) -> Dict:
        """
        获取题材强度排行榜

        Args:
            sort_by: 排序字段 (hot_score/limit_up_count/continuous_days)
            limit: 返回数量

        Returns:
            排行榜数据
        """
        redis_client = self._get_redis()
        cache_key = f"theme:ranking:{sort_by}:{limit}"

        # 尝试从缓存获取
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis 读取失败: {e}")

        # 获取题材库数据
        library_data = self.get_theme_library(limit=100)
        
        if library_data.get('status') != 'success':
            return library_data

        themes = library_data.get('data', [])
        
        # 排序
        valid_sort_fields = ['hot_score', 'limit_up_count', 'continuous_days', 'change_pct']
        if sort_by not in valid_sort_fields:
            sort_by = 'hot_score'
        
        themes.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
        themes = themes[:limit]

        result = {
            'status': 'success',
            'data': themes,
            'count': len(themes),
            'sort_by': sort_by,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 写入缓存
        if redis_client:
            try:
                redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(result, ensure_ascii=False)
                )
            except Exception as e:
                logger.warning(f"Redis 写入失败: {e}")

        return result

    def get_limit_up_theme_distribution(self) -> Dict:
        """
        获取涨停题材分布统计

        Returns:
            涨停题材分布数据
        """
        redis_client = self._get_redis()
        cache_key = "theme:limit_up_distribution"

        # 尝试从缓存获取
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis 读取失败: {e}")

        try:
            # 获取题材库数据
            library_data = self.get_theme_library(limit=100)
            themes = library_data.get('data', [])

            # 统计分布
            total_limit_up = sum(t.get('limit_up_count', 0) for t in themes)
            
            distribution = []
            for theme in themes:
                if theme.get('limit_up_count', 0) > 0:
                    percentage = (theme['limit_up_count'] / total_limit_up * 100) if total_limit_up > 0 else 0
                    distribution.append({
                        'theme_name': theme['theme_name'],
                        'limit_up_count': theme['limit_up_count'],
                        'percentage': round(percentage, 2),
                        'lifecycle': theme['lifecycle'],
                        'hot_score': theme['hot_score']
                    })

            # 按涨停数排序
            distribution.sort(key=lambda x: x['limit_up_count'], reverse=True)

            # 统计生命周期分布
            lifecycle_stats = {
                self.LIFECYCLE_FERMENT: 0,
                self.LIFECYCLE_BOOM: 0,
                self.LIFECYCLE_DECLINE: 0
            }
            for theme in themes:
                lifecycle = theme.get('lifecycle', self.LIFECYCLE_FERMENT)
                if lifecycle in lifecycle_stats:
                    lifecycle_stats[lifecycle] += 1

            result = {
                'status': 'success',
                'data': {
                    'total_limit_up': total_limit_up,
                    'theme_count': len(distribution),
                    'distribution': distribution[:20],  # 前20个题材
                    'lifecycle_stats': lifecycle_stats
                },
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 写入缓存
            if redis_client:
                try:
                    redis_client.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(result, ensure_ascii=False)
                    )
                except Exception as e:
                    logger.warning(f"Redis 写入失败: {e}")

            return result

        except Exception as e:
            logger.error(f"获取涨停题材分布失败: {e}")
            return {
                'status': 'error',
                'data': {},
                'message': str(e)
            }

    def get_theme_detail(self, theme_name: str) -> Dict:
        """
        获取题材详情

        Args:
            theme_name: 题材名称

        Returns:
            题材详情数据
        """
        try:
            # 获取题材库数据
            library_data = self.get_theme_library(limit=100)
            themes = library_data.get('data', [])

            # 查找指定题材
            for theme in themes:
                if theme.get('theme_name') == theme_name:
                    # 获取历史趋势
                    history = self.theme_history.get(theme_name, [])
                    theme['history'] = history
                    
                    return {
                        'status': 'success',
                        'data': theme
                    }

            return {
                'status': 'error',
                'message': f'题材不存在: {theme_name}'
            }

        except Exception as e:
            logger.error(f"获取题材详情失败: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }


# 全局单例
_theme_library_service: Optional[ThemeLibraryService] = None


def get_theme_library_service(redis_client=None) -> ThemeLibraryService:
    """获取题材库服务实例"""
    global _theme_library_service
    if _theme_library_service is None:
        _theme_library_service = ThemeLibraryService(redis_client)
    return _theme_library_service
