"""
连板天梯服务 - Limit Up Ladder Service
获取连续涨停股票数据

功能：
- 从 AKShare 获取每日涨停数据
- 计算连续涨停板数
- Redis 缓存支持
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import redis
from threading import Lock

logger = logging.getLogger(__name__)


class LimitUpLadderService:
    """连板天梯服务"""

    _instance = None
    _lock = Lock()

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.cache_ttl = 300  # 缓存 5 分钟

    @classmethod
    def get_instance(cls, redis_client=None) -> 'LimitUpLadderService':
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

    def _get_akshare_limit_up(self, date: str = None) -> pd.DataFrame:
        """
        从 AKShare 获取涨停数据

        Args:
            date: 日期，格式 YYYYMMDD，默认最新交易日

        Returns:
            涨停股票 DataFrame
        """
        try:
            import akshare as ak

            # 获取涨停股票数据
            if date:
                df = ak.stock_zt_pool_em(date=date)
            else:
                # 获取最新交易日数据
                df = ak.stock_zt_pool_em()

            return df

        except Exception as e:
            logger.error(f"获取涨停数据失败: {e}")
            return pd.DataFrame()

    def _calculate_consecutive_limit_ups(self, limit_up_df: pd.DataFrame, days: int = 30) -> List[Dict]:
        """
        计算连续涨停

        Args:
            limit_up_df: 涨停数据
            days: 追溯天数

        Returns:
            连续涨停股票列表
        """
        if limit_up_df.empty:
            return []

        # 获取最近 N 个交易日的涨停数据
        all_limit_ups = {}
        
        # 获取历史涨停数据需要逐日查询，这里简化为使用当日数据
        # 后续可以扩展为多日查询
        
        result = []
        for _, row in limit_up_df.iterrows():
            try:
                stock_code = str(row.get('代码', ''))
                stock_name = str(row.get('名称', ''))
                
                # 跳过 ST 股
                if 'ST' in stock_name or '*ST' in stock_name:
                    continue

                # 获取连板数（从涨停原因中解析）
                reason = str(row.get('涨停原因', ''))
                consecutive = 1
                if '第' in reason and '板' in reason:
                    # 尝试从原因中提取连板数
                    import re
                    match = re.search(r'第(\d+)板', reason)
                    if match:
                        consecutive = int(match.group(1))

                # 计算封板强度
                first_limit_price = row.get('首次封板时间', '')
                last_limit_price = row.get('最后封板时间', '')
                maintain_time = row.get('板上换手率(%)', 0)  # 近似用换手率
                
                # 涨跌幅
                change_pct = row.get('涨跌幅(%)', 0)

                result.append({
                    'symbol': stock_code,
                    'name': stock_name,
                    'consecutive_days': consecutive,
                    'change_pct': float(change_pct) if change_pct else 0,
                    'limit_time': first_limit_price,
                    'last_limit_time': last_limit_price,
                    'maintain_strength': float(maintain_time) if maintain_time else 0,
                    'reason': reason,
                    'price': float(row.get('最新价', 0)) if row.get('最新价') else 0,
                })
            except Exception as e:
                logger.warning(f"处理涨停数据行失败: {e}")
                continue

        # 按连板数降序排序
        result.sort(key=lambda x: x['consecutive_days'], reverse=True)
        
        return result

    def get_limit_up_ladder(self, min_consecutive: int = 2, limit: int = 50) -> Dict:
        """
        获取连板天梯数据

        Args:
            min_consecutive: 最少连续涨停天数
            limit: 返回数量限制

        Returns:
            连板天梯数据
        """
        redis_client = self._get_redis()
        cache_key = f"stock:limit_up_ladder:{min_consecutive}:{limit}"

        # 尝试从缓存获取
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info("从 Redis 缓存获取连板天梯数据")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis 读取失败: {e}")

        # 获取实时数据
        try:
            limit_up_df = self._get_akshare_limit_up()
            
            if limit_up_df.empty:
                return {
                    'status': 'success',
                    'data': [],
                    'count': 0,
                    'message': '暂无涨停数据'
                }

            ladder_data = self._calculate_consecutive_limit_ups(limit_up_df)

            # 过滤最小连板数
            if min_consecutive > 1:
                ladder_data = [x for x in ladder_data if x['consecutive_days'] >= min_consecutive]

            # 限制数量
            ladder_data = ladder_data[:limit]

            # 统计信息
            stats = {
                'total_count': len(ladder_data),
                'consecutive_2': len([x for x in ladder_data if x['consecutive_days'] == 2]),
                'consecutive_3': len([x for x in ladder_data if x['consecutive_days'] == 3]),
                'consecutive_4': len([x for x in ladder_data if x['consecutive_days'] == 4]),
                'consecutive_5_plus': len([x for x in ladder_data if x['consecutive_days'] >= 5]),
            }

            result = {
                'status': 'success',
                'data': ladder_data,
                'count': len(ladder_data),
                'stats': stats,
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
            logger.error(f"获取连板天梯失败: {e}")
            return {
                'status': 'error',
                'data': [],
                'count': 0,
                'message': str(e)
            }

    def get_today_limit_up(self, limit: int = 100) -> Dict:
        """
        获取今日涨停板（不含连板统计）

        Args:
            limit: 返回数量限制

        Returns:
            今日涨停数据
        """
        redis_client = self._get_redis()
        cache_key = f"stock:today_limit_up:{limit}"

        # 尝试从缓存获取
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info("从 Redis 缓存获取今日涨停数据")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis 读取失败: {e}")

        try:
            limit_up_df = self._get_akshare_limit_up()

            if limit_up_df.empty:
                return {
                    'status': 'success',
                    'data': [],
                    'count': 0,
                    'message': '暂无涨停数据'
                }

            result_list = []
            for _, row in limit_up_df.iterrows():
                try:
                    result_list.append({
                        'symbol': str(row.get('代码', '')),
                        'name': str(row.get('名称', '')),
                        'price': float(row.get('最新价', 0)) if row.get('最新价') else 0,
                        'change_pct': float(row.get('涨跌幅(%)', 0)) if row.get('涨跌幅(%)') else 0,
                        'reason': str(row.get('涨停原因', '')),
                        'first_limit_time': str(row.get('首次封板时间', '')),
                        'last_limit_time': str(row.get('最后封板时间', '')),
                        'turnover': float(row.get('成交额(亿元)', 0)) if row.get('成交额(亿元)') else 0,
                    })
                except Exception:
                    continue

            result = {
                'status': 'success',
                'data': result_list,
                'count': len(result_list),
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
            logger.error(f"获取今日涨停失败: {e}")
            return {
                'status': 'error',
                'data': [],
                'count': 0,
                'message': str(e)
            }


# 全局单例
_limit_up_ladder_service: Optional[LimitUpLadderService] = None


def get_limit_up_ladder_service(redis_client=None) -> LimitUpLadderService:
    """获取连板天梯服务实例"""
    global _limit_up_ladder_service
    if _limit_up_ladder_service is None:
        _limit_up_ladder_service = LimitUpLadderService(redis_client)
    return _limit_up_ladder_service
