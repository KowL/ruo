"""
股票筛选器节点 - 根据条件筛选股票或处理指定股票
"""
import akshare as ak
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import sys
import os

# 添加utils目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.core.data_converter import safe_convert_to_python_types, safe_float, safe_int, safe_str

from app.llm_agent.state.stock_analysis_state import StockAnalysisState, StockInfo

logger = logging.getLogger(__name__)

class StockFilter:
    """股票筛选器"""

    def __init__(self):
        self.default_conditions = {
            "market_cap_min": 50,  # 最小市值(亿)
            "market_cap_max": 2000,  # 最大市值(亿)
            "pe_min": 5,  # 最小PE
            "pe_max": 100,  # 最大PE
            "turnover_rate_min": 1,  # 最小换手率
            "change_pct_min": -10,  # 最小涨跌幅
            "change_pct_max": 20,  # 最大涨跌幅
            "exclude_st": True,  # 排除ST股票
            "exclude_new": True,  # 排除次新股
            "min_listing_days": 365,  # 最小上市天数
            "sectors": [],  # 指定板块
            "concepts": [],  # 指定概念
            "max_stocks": 20,  # 最大股票数量
        }

    def filter_stocks(self, state: StockAnalysisState) -> StockAnalysisState:
        """主要筛选逻辑"""
        try:
            logger.info("开始股票筛选...")

            # 获取筛选条件
            conditions = {**self.default_conditions, **(state.get("filter_conditions", {}))}

            # 根据分析类型处理
            if state["analysis_type"] == "specified":
                # 处理指定股票
                selected_stocks = self._process_specified_stocks(state["target_stocks"])
                filter_summary = f"处理指定股票 {len(selected_stocks)} 只"

            elif state["analysis_type"] == "filtered":
                # 根据条件筛选
                selected_stocks = self._filter_by_conditions(conditions)
                filter_summary = f"根据筛选条件找到 {len(selected_stocks)} 只股票"

            else:  # mixed
                # 混合模式：指定股票 + 条件筛选
                specified_stocks = self._process_specified_stocks(state.get("target_stocks", []))
                filtered_stocks = self._filter_by_conditions(conditions)

                # 合并并去重
                all_stocks = {stock["code"]: stock for stock in specified_stocks + filtered_stocks}
                selected_stocks = list(all_stocks.values())

                filter_summary = f"指定股票 {len(specified_stocks)} 只，筛选股票 {len(filtered_stocks)} 只，合并后 {len(selected_stocks)} 只"

            # 更新状态
            state["selected_stocks"] = selected_stocks
            state["filter_summary"] = filter_summary
            state["next_action"] = "sector_analysis"

            logger.info(f"股票筛选完成: {filter_summary}")
            return state

        except Exception as e:
            logger.error(f"股票筛选失败: {str(e)}")
            state["error"] = f"股票筛选失败: {str(e)}"
            return state

    def _process_specified_stocks(self, stock_codes: List[str]) -> List[StockInfo]:
        """处理指定的股票代码"""
        if not stock_codes:
            return []

        stocks = []
        for code in stock_codes:
            try:
                stock_info = self._get_stock_info(code)
                if stock_info:
                    stocks.append(stock_info)
            except Exception as e:
                logger.warning(f"获取股票 {code} 信息失败: {str(e)}")

        return stocks

    def _filter_by_conditions(self, conditions: Dict[str, Any]) -> List[StockInfo]:
        """根据条件筛选股票"""
        try:
            # 获取股票基础数据
            stock_data = self._get_stock_basic_data()

            # 应用筛选条件
            filtered_data = self._apply_filters(stock_data, conditions)

            # 转换为StockInfo格式
            stocks = []
            for _, row in filtered_data.head(conditions["max_stocks"]).iterrows():
                stock_info = self._row_to_stock_info(row)
                if stock_info:
                    stocks.append(stock_info)

            return stocks

        except Exception as e:
            logger.error(f"条件筛选失败: {str(e)}")
            return []

    def _get_stock_basic_data(self) -> pd.DataFrame:
        """获取股票基础数据"""
        try:
            # 获取实时行情数据
            df = ak.stock_zh_a_spot_em()

            # 数据清洗和标准化
            df = df.rename(columns={
                "代码": "code",
                "名称": "name",
                "最新价": "price",
                "涨跌幅": "change_pct",
                "成交量": "volume",
                "换手率": "turnover_rate",
                "总市值": "market_cap",
                "市盈率-动态": "pe_ratio",
                "市净率": "pb_ratio"
            })

            # 数据类型转换
            numeric_columns = ["price", "change_pct", "volume", "turnover_rate", "market_cap", "pe_ratio", "pb_ratio"]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            return df

        except Exception as e:
            logger.error(f"获取股票基础数据失败: {str(e)}")
            return pd.DataFrame()

    def _apply_filters(self, df: pd.DataFrame, conditions: Dict[str, Any]) -> pd.DataFrame:
        """应用筛选条件"""
        if df.empty:
            return df

        # 市值筛选
        if "market_cap_min" in conditions and conditions["market_cap_min"]:
            df = df[df["market_cap"] >= conditions["market_cap_min"] * 100000000]  # 转换为元

        if "market_cap_max" in conditions and conditions["market_cap_max"]:
            df = df[df["market_cap"] <= conditions["market_cap_max"] * 100000000]

        # PE筛选
        if "pe_min" in conditions and conditions["pe_min"]:
            df = df[df["pe_ratio"] >= conditions["pe_min"]]

        if "pe_max" in conditions and conditions["pe_max"]:
            df = df[df["pe_ratio"] <= conditions["pe_max"]]

        # 换手率筛选
        if "turnover_rate_min" in conditions and conditions["turnover_rate_min"]:
            df = df[df["turnover_rate"] >= conditions["turnover_rate_min"]]

        # 涨跌幅筛选
        if "change_pct_min" in conditions and conditions["change_pct_min"] is not None:
            df = df[df["change_pct"] >= conditions["change_pct_min"]]

        if "change_pct_max" in conditions and conditions["change_pct_max"] is not None:
            df = df[df["change_pct"] <= conditions["change_pct_max"]]

        # 排除ST股票
        if conditions.get("exclude_st", True):
            df = df[~df["name"].str.contains("ST|\\*ST", na=False)]

        # 按涨跌幅排序
        df = df.sort_values("change_pct", ascending=False)

        return df

    def _get_stock_info(self, code: str) -> Optional[StockInfo]:
        """获取单个股票信息"""
        try:
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            stock_row = df[df["代码"] == code]

            if stock_row.empty:
                logger.warning(f"未找到股票 {code}")
                return None

            row = stock_row.iloc[0]
            return self._row_to_stock_info(row)

        except Exception as e:
            logger.error(f"获取股票 {code} 信息失败: {str(e)}")
            return None

    def _row_to_stock_info(self, row) -> Optional[StockInfo]:
        """将DataFrame行转换为StockInfo"""
        try:
            # 获取板块和概念信息
            code = safe_str(row.get("代码", row.get("code", "")))
            sector, concepts = self._get_stock_sector_concept(code)

            # 安全转换所有数值，确保使用Python原生类型
            stock_info: StockInfo = {
                "code": code,
                "name": safe_str(row.get("名称", row.get("name", ""))),
                "price": safe_float(row.get("最新价", row.get("price", 0))) or 0.0,
                "change_pct": safe_float(row.get("涨跌幅", row.get("change_pct", 0))) or 0.0,
                "volume": safe_int(row.get("成交量", row.get("volume", 0))) or 0,
                "turnover_rate": safe_float(row.get("换手率", row.get("turnover_rate", 0))) or 0.0,
                "market_cap": safe_float(row.get("总市值", row.get("market_cap", 0))) or 0.0,
                "pe_ratio": safe_float(row.get("市盈率-动态", row.get("pe_ratio"))),
                "pb_ratio": safe_float(row.get("市净率", row.get("pb_ratio"))),
                "sector": sector,
                "concept": concepts
            }

            # 确保所有数据都是Python原生类型
            stock_info = safe_convert_to_python_types(stock_info)
            return stock_info

        except Exception as e:
            logger.error(f"转换股票信息失败: {str(e)}")
            return None

    def _get_stock_sector_concept(self, code: str) -> tuple[str, List[str]]:
        """获取股票板块和概念信息"""
        try:
            # 获取股票概念信息
            concept_df = ak.stock_board_concept_cons_em(symbol=code)
            concepts = concept_df["板块名称"].tolist() if not concept_df.empty else []

            # 获取行业信息
            try:
                industry_df = ak.stock_board_industry_cons_em(symbol=code)
                sector = industry_df["板块名称"].iloc[0] if not industry_df.empty else "未知"
            except:
                sector = "未知"

            return sector, concepts[:5]  # 限制概念数量

        except Exception as e:
            logger.warning(f"获取股票 {code} 板块概念信息失败: {str(e)}")
            return "未知", []

    def _safe_float(self, value) -> Optional[float]:
        """安全转换为浮点数"""
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except:
            return None

def stock_filter_node(state: StockAnalysisState) -> StockAnalysisState:
    """股票筛选器节点入口函数"""
    filter_agent = StockFilter()
    return filter_agent.filter_stocks(state)