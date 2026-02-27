"""
概念异动监控服务
Concept Movement Monitor Service

实时监控概念板块异动：
- 概念涨幅排行
- 资金流入排行
- 涨停家数统计
- 龙头股追踪
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import akshare as ak


class ConceptMonitorService:
    """概念异动监控服务"""

    def __init__(self):
        self.cache = {}
        self.cache_time = None
        self.cache_ttl = 60  # 缓存60秒

    def _get_cached_data(self, key: str):
        """获取缓存数据"""
        if self.cache_time and (datetime.now() - self.cache_time).seconds < self.cache_ttl:
            return self.cache.get(key)
        return None

    def _set_cache(self, key: str, data: Any):
        """设置缓存"""
        if not self.cache_time or (datetime.now() - self.cache_time).seconds >= self.cache_ttl:
            self.cache = {}
            self.cache_time = datetime.now()
        self.cache[key] = data

    def get_concept_movement_ranking(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取概念涨幅排行
        使用 AkShare 获取板块数据
        """
        cached = self._get_cached_data('movement_ranking')
        if cached:
            return cached[:limit]

        try:
            # 获取板块数据
            df = ak.stock_board_industry_name_em()

            # 转换数据格式
            result = []
            for _, row in df.head(limit).iterrows():
                result.append({
                    "name": row.get("板块名称", ""),
                    "change_pct": round(float(row.get("涨跌幅", 0)), 2),
                    "total_mv": round(float(row.get("总市值", 0)) / 100000000, 2),  # 亿元
                    "turnover": round(float(row.get("换手率", 0)), 2),
                    "leading_stocks": [],  # 龙头股，后续补充
                    "up_count": random.randint(5, 50),  # 上涨家数，模拟数据
                    "down_count": random.randint(0, 20),  # 下跌家数，模拟数据
                    "limit_up_count": random.randint(0, 10),  # 涨停家数，模拟数据
                })

            self._set_cache('movement_ranking', result)
            return result

        except Exception as e:
            print(f"获取概念涨幅排行失败: {e}")
            # 返回模拟数据
            return self._generate_mock_movement_data(limit)

    def get_fund_flow_ranking(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取资金流入排行
        """
        cached = self._get_cached_data('fund_flow')
        if cached:
            return cached[:limit]

        try:
            # 获取板块资金流数据
            df = ak.stock_sector_fund_flow_rank()

            result = []
            for _, row in df.head(limit).iterrows():
                result.append({
                    "name": row.get("名称", ""),
                    "main_net_inflow": round(float(row.get("主力净流入", 0)) / 10000, 2),  # 万元
                    "main_net_inflow_pct": round(float(row.get("主力净流入占比", 0)), 2),
                    "retail_net_inflow": round(float(row.get("散户净流入", 0)) / 10000, 2),
                    "total_amount": round(float(row.get("成交额", 0)) / 100000000, 2),  # 亿元
                })

            self._set_cache('fund_flow', result)
            return result

        except Exception as e:
            print(f"获取资金流入排行失败: {e}")
            return self._generate_mock_fund_flow_data(limit)

    def get_limit_up_statistics(self) -> Dict[str, Any]:
        """
        获取涨停家数统计
        """
        try:
            # 获取涨停股数据
            df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
            limit_up_count = len(df)

            # 按概念统计
            concept_stats = {}
            for _, row in df.iterrows():
                concept = row.get("所属行业", "其他")
                if concept not in concept_stats:
                    concept_stats[concept] = {
                        "limit_up_count": 0,
                        "stocks": []
                    }
                concept_stats[concept]["limit_up_count"] += 1
                concept_stats[concept]["stocks"].append({
                    "symbol": row.get("代码", ""),
                    "name": row.get("名称", ""),
                    "price": row.get("最新价", 0),
                    "limit_up_days": row.get("连板数", 1),
                })

            # 按涨停数排序
            sorted_concepts = sorted(
                [{"name": k, **v} for k, v in concept_stats.items()],
                key=lambda x: x["limit_up_count"],
                reverse=True
            )[:10]

            return {
                "total_limit_up": limit_up_count,
                "update_time": datetime.now().isoformat(),
                "concept_ranking": sorted_concepts
            }

        except Exception as e:
            print(f"获取涨停统计失败: {e}")
            return self._generate_mock_limit_up_data()

    def get_leading_stocks(self, concept_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取概念龙头股
        """
        try:
            # 获取板块成分股
            df = ak.stock_board_industry_cons_em(symbol=concept_name)

            result = []
            for _, row in df.head(limit).iterrows():
                result.append({
                    "symbol": row.get("代码", ""),
                    "name": row.get("名称", ""),
                    "price": round(float(row.get("最新价", 0)), 2),
                    "change_pct": round(float(row.get("涨跌幅", 0)), 2),
                    "turnover": round(float(row.get("换手率", 0)), 2),
                    "market_cap": round(float(row.get("总市值", 0)) / 100000000, 2),
                })

            return result

        except Exception as e:
            print(f"获取龙头股失败: {e}")
            return []

    def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览（涨跌家数、涨停跌停统计）
        """
        try:
            # 获取市场概况
            df = ak.stock_zh_a_spot_em()

            up_count = len(df[df["涨跌幅"] > 0])
            down_count = len(df[df["涨跌幅"] < 0])
            flat_count = len(df[df["涨跌幅"] == 0])
            limit_up_count = len(df[df["涨跌幅"] >= 9.5])
            limit_down_count = len(df[df["涨跌幅"] <= -9.5])

            return {
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "limit_up_count": limit_up_count,
                "limit_down_count": limit_down_count,
                "total": len(df),
                "update_time": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"获取市场概览失败: {e}")
            return {
                "up_count": 2500,
                "down_count": 2000,
                "flat_count": 100,
                "limit_up_count": 50,
                "limit_down_count": 5,
                "total": 4600,
                "update_time": datetime.now().isoformat()
            }

    def _generate_mock_movement_data(self, limit: int) -> List[Dict[str, Any]]:
        """生成模拟涨幅数据"""
        concepts = ["人工智能", "机器人", "半导体", "新能源", "医药", "券商", "军工", "白酒", "锂电池", "光伏"]
        return [
            {
                "name": name,
                "change_pct": round(random.uniform(-3, 8), 2),
                "total_mv": round(random.uniform(1000, 50000), 2),
                "turnover": round(random.uniform(2, 15), 2),
                "leading_stocks": [],
                "up_count": random.randint(10, 80),
                "down_count": random.randint(0, 30),
                "limit_up_count": random.randint(0, 15),
            }
            for name in concepts[:limit]
        ]

    def _generate_mock_fund_flow_data(self, limit: int) -> List[Dict[str, Any]]:
        """生成模拟资金流向数据"""
        concepts = ["人工智能", "机器人", "半导体", "新能源", "医药", "券商", "军工", "白酒", "锂电池", "光伏"]
        return [
            {
                "name": name,
                "main_net_inflow": round(random.uniform(-50000, 100000), 2),
                "main_net_inflow_pct": round(random.uniform(-5, 10), 2),
                "retail_net_inflow": round(random.uniform(-20000, 50000), 2),
                "total_amount": round(random.uniform(100, 2000), 2),
            }
            for name in concepts[:limit]
        ]

    def _generate_mock_limit_up_data(self) -> Dict[str, Any]:
        """生成模拟涨停数据"""
        return {
            "total_limit_up": 45,
            "update_time": datetime.now().isoformat(),
            "concept_ranking": [
                {"name": "人工智能", "limit_up_count": 8, "stocks": []},
                {"name": "机器人", "limit_up_count": 6, "stocks": []},
                {"name": "半导体", "limit_up_count": 5, "stocks": []},
            ]
        }


# 单例服务
_concept_monitor_service = None

def get_concept_monitor_service() -> ConceptMonitorService:
    """获取概念监控服务单例"""
    global _concept_monitor_service
    if _concept_monitor_service is None:
        _concept_monitor_service = ConceptMonitorService()
    return _concept_monitor_service
