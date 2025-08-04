#!/usr/bin/env python3
"""
AKShare数据源工具
提供AKShare数据获取的统一接口
"""

import pandas as pd
from datetime import date
from typing import Optional, Dict, Any, List
import warnings
warnings.filterwarnings('ignore')

class AKShareProvider:
    """AKShare数据提供器"""
    
    def __init__(self):
        """初始化AKShare提供器"""
        try:
            import akshare as ak
            self.ak = ak
            self.connected = True
            print("✅ AKShare初始化成功")
        except ImportError:
            self.ak = None
            self.connected = False
            print("❌ AKShare未安装")
    
    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        if not self.connected:
            return None
        
        try:
            # 转换股票代码格式
            if len(symbol) == 6:
                symbol = symbol
            else:
                symbol = symbol.replace('.SZ', '').replace('.SS', '')
            
            # 获取数据
            data = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace('-', '') if start_date else "20240101",
                end_date=end_date.replace('-', '') if end_date else "20241231",
                adjust=""
            )
            
            return data
            
        except Exception as e:
            print(f"❌ AKShare获取股票数据失败: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        if not self.connected:
            return {}
        
        try:
            # 获取股票基本信息
            stock_list = self.ak.stock_info_a_code_name()
            stock_info = stock_list[stock_list['code'] == symbol]
            
            if not stock_info.empty:
                return {
                    'symbol': symbol,
                    'name': stock_info.iloc[0]['name'],
                    'source': 'akshare'
                }
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}
                
        except Exception as e:
            print(f"❌ AKShare获取股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}

    def get_stock_technical_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """获取股票技术指标数据
        
        Args:
            symbol: 股票代码
            days: 获取天数
            
        Returns:
            技术指标数据DataFrame
        """
        if not self.connected:
            return None
            
        try:
            from datetime import datetime, timedelta
            import stockstats
            
            # 计算起始日期
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            # 获取历史数据
            hist_data = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            
            if hist_data.empty:
                return None
            
            # 重命名列以符合stockstats要求
            hist_data = hist_data.rename(columns={
                '开盘': 'open',
                '收盘': 'close', 
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })
            
            # 计算技术指标
            stock = stockstats.StockDataFrame.retype(hist_data)
            
            # 添加常用技术指标
            stock['ma5'] = stock['close_5_sma']  # 5日均线
            stock['ma20'] = stock['close_20_sma']  # 20日均线
            stock['rsi'] = stock['rsi_14']  # RSI指标
            stock['macd'] = stock['macd']  # MACD
            stock['volume_ma5'] = stock['volume_5_sma']  # 成交量5日均线
            
            return stock.tail(1)  # 返回最新一天的数据
            
        except Exception as e:
            print(f"❌ 获取技术指标数据失败: {e}")
            return None

    def get_stock_lhb_data(self, trade_date: date) -> Dict[str, Dict[str, Any]]:
        """获取指定日期的龙虎榜数据

        Args:
            trade_date: 交易日期

        Returns:
            Dict[str, Dict[str, Any]]: 股票代码到龙虎榜数据的映射
        """
        if not self.connected:
            return {}
        
        try:
            # 格式化日期为YYYYMMDD
            date_str = trade_date.replace("-", "")
            
            # 获取龙虎榜数据
            lhb_df = self.ak.stock_lhb_detail_em(date_str, date_str)
            
            if lhb_df.empty:
                print(f"❌ 未获取到 {trade_date} 的龙虎榜数据")
                return {}
            
            print(f"📊 获取到 {len(lhb_df)} 条龙虎榜记录")
            print("数据列名:", lhb_df.columns.tolist())
            
            # 转换为字典格式
            result = {}
            
            # 检查必需的列是否存在
            required_columns = ['代码', '名称']
            missing_columns = [col for col in required_columns if col not in lhb_df.columns]
            if missing_columns:
                print(f"❌ 缺失必需列: {missing_columns}")
                return {}
            
            # 获取当日所有上榜股票
            stock_codes = lhb_df['代码'].unique()
            
            for code in stock_codes:
                try:
                    # 获取该股票的所有记录
                    stock_data = lhb_df[lhb_df['代码'] == code]
                    
                    if stock_data.empty:
                        continue
                    
                    # 基本信息
                    base_info = stock_data.iloc[0]
                    
                    # 尝试获取买卖席位信息（如果存在）
                    buy_seats = []
                    sell_seats = []
                    
                    # 检查是否有买卖方向列
                    if '买卖方向' in lhb_df.columns:
                        # 买入席位
                        buy_records = stock_data[stock_data['买卖方向'] == '买入']
                        for _, row in buy_records.iterrows():
                            buy_seats.append({
                                "营业部": row.get('营业部名称', '未知营业部'),
                                "买入金额": row.get('买入金额', 0)
                            })
                        
                        # 卖出席位
                        sell_records = stock_data[stock_data['买卖方向'] == '卖出']
                        for _, row in sell_records.iterrows():
                            sell_seats.append({
                                "营业部": row.get('营业部名称', '未知营业部'),
                                "卖出金额": row.get('卖出金额', 0)
                            })
                    else:
                        # 如果没有详细席位信息，创建基础数据
                        buy_seats = [{"营业部": "数据不详", "买入金额": 0}]
                        sell_seats = [{"营业部": "数据不详", "卖出金额": 0}]
                    
                    # 计算机构数量
                    buy_inst_count = len([s for s in buy_seats if '机构专用' in s['营业部']])
                    sell_inst_count = len([s for s in sell_seats if '机构专用' in s['营业部']])
                    
                    # 计算机构净买额
                    inst_buy_amount = sum([s['买入金额'] for s in buy_seats if '机构专用' in s['营业部']])
                    inst_sell_amount = sum([s['卖出金额'] for s in sell_seats if '机构专用' in s['营业部']])
                    inst_net_amount = inst_buy_amount - inst_sell_amount
                    
                    # 获取技术指标数据
                    tech_data = self.get_stock_technical_data(code)
                    tech_indicators = {}
                    if tech_data is not None and not tech_data.empty:
                        tech_indicators = {
                            "ma5": float(tech_data['ma5'].iloc[-1]) if 'ma5' in tech_data.columns else None,
                            "ma20": float(tech_data['ma20'].iloc[-1]) if 'ma20' in tech_data.columns else None,
                            "rsi": float(tech_data['rsi'].iloc[-1]) if 'rsi' in tech_data.columns else None,
                            "macd": float(tech_data['macd'].iloc[-1]) if 'macd' in tech_data.columns else None,
                            "volume_ma5": float(tech_data['volume_ma5'].iloc[-1]) if 'volume_ma5' in tech_data.columns else None
                        }
                    
                    # 获取基础数据，使用安全的字典访问
                    net_amount = base_info.get('净买额', 0)
                    buy_amount = base_info.get('买入金额', 0) 
                    sell_amount = base_info.get('卖出金额', 0)
                    close_price = base_info.get('收盘价', 0)
                    change_pct = base_info.get('涨跌幅', 0)
                    
                    # 计算资金流向强度和机构参与度
                    total_amount = buy_amount + sell_amount
                    net_flow_ratio = net_amount / total_amount if total_amount > 0 else 0
                    inst_participation = (buy_inst_count + sell_inst_count) / len(buy_seats + sell_seats) if (buy_seats + sell_seats) else 0
                    
                    result[code] = {
                        "股票代码": code,
                        "股票名称": base_info.get('名称', f'股票{code}'),
                        "解读": base_info.get('解读', '龙虎榜'),
                        "收盘价": close_price,
                        "涨跌幅": change_pct,
                        "龙虎榜净买额": net_amount,
                        "龙虎榜买入额": buy_amount,
                        "龙虎榜卖出额": sell_amount,
                        "买方机构数": buy_inst_count,
                        "卖方机构数": sell_inst_count,
                        "机构净买额": inst_net_amount,
                        "买方席位": buy_seats,
                        "卖方席位": sell_seats,
                        "技术指标": tech_indicators,
                        "资金流向强度": net_flow_ratio,
                        "机构参与度": inst_participation,
                        "分析指标": {
                            "总成交金额": total_amount,
                            "机构买入金额": inst_buy_amount,
                            "机构卖出金额": inst_sell_amount,
                            "净资金流入": net_amount > 0,
                            "机构净流入": inst_net_amount > 0,
                            "涨幅较大": abs(change_pct) > 5,
                            "成交活跃": total_amount > 50000000  # 5千万
                        }
                    }
                    
                except Exception as e:
                    print(f"❌ 处理股票 {code} 数据失败: {e}")
                    continue
            
            print(f"✅ 成功解析 {len(result)} 只股票的龙虎榜数据")
            return result
            
        except Exception as e:
            print(f"❌ AKShare获取龙虎榜数据失败: {e}")
            return {}

def get_akshare_provider() -> AKShareProvider:
    """获取AKShare提供器实例"""
    return AKShareProvider()

def get_stock_lhb_data(trade_date: str) -> Dict[str, Dict[str, Any]]:
    """便捷函数：获取指定日期的龙虎榜数据

    Args:
        trade_date: 交易日期

    Returns:
        Dict[str, Dict[str, Any]]: 股票代码到龙虎榜数据的映射
    """
    provider = get_akshare_provider()
    return provider.get_stock_lhb_data(trade_date)
