import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import datetime
import logging
import json
import os
import pandas as pd
from typing import List, Tuple, Optional, Dict
from contextlib import contextmanager
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 引入项目的LLM基础设施
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from tradingagents.llm_adapters import ChatDashScope, ChatDashScopeOpenAI
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.akshare_utils import AKShareProvider

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/stock_monitor.log'),
        logging.StreamHandler()
    ]
)

# 默认配置
DEFAULT_CONFIG = {
    'fluctuation_threshold': 0.0,  # 触发AI分析的波动阈值（百分比）
    'monitor_interval': 30,  # 监控间隔（秒）
    'db_path': 'ruo.db',
    'enable_notifications': True,
    # 继承项目的LLM配置
    'llm_provider': DEFAULT_CONFIG.get('llm_provider', 'dashscope'),
    'deep_think_llm': DEFAULT_CONFIG.get('deep_think_llm', 'qwen-plus'),
    'quick_think_llm': DEFAULT_CONFIG.get('quick_think_llm', 'qwen-turbo'),
    'backend_url': DEFAULT_CONFIG.get('backend_url', 'https://api.openai.com/v1'),
}

@contextmanager
def get_db_connection(db_path: str = 'ruo.db'):
    """数据库连接上下文管理器"""
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

def init_database(db_path: str = 'ruo.db'):
    """初始化数据库表"""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # 创建价格历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                price REAL NOT NULL
            )
        ''')
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_prices_stock_timestamp 
            ON stock_prices(stock, timestamp)
        ''')
        # 确保stock_hold表存在
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_hold (
                stock TEXT PRIMARY KEY,
                name TEXT,
                hold_num INTEGER,
                available INTEGER,
                cost REAL
            )
        ''')
        conn.commit()

def get_portfolio_stocks(db_path: str = 'ruo.db') -> List[Tuple[str, str, int, int, float]]:
    """从 stock_hold 表获取监控股票及其持仓数据"""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT stock, name, hold_num, available, cost FROM stock_hold")
        return cursor.fetchall()  # 返回列表: [('AAPL', '苹果', 100, 50, 150.0), ...]


def get_current_price(stock: str) -> Optional[float]:
    """从Yahoo Finance获取当前价格"""
    try:
        ticker = yf.Ticker(stock)
        data = ticker.history(period='1d')
        if data.empty:
            logging.warning(f"No data available for {stock}")
            return None
        current_price = float(data['Close'].iloc[-1])
        logging.debug(f"Retrieved price for {stock}: {current_price}")
        return current_price
    except Exception as e:
        logging.error(f"Failed to get price for {stock}: {e}")
        return None

def get_chinese_stock_price_and_tech(stock: str, akshare_provider: AKShareProvider = None) -> Tuple[Optional[float], Dict]:
    """获取中国股票价格和技术指标"""
    if akshare_provider is None:
        akshare_provider = AKShareProvider()
    
    try:
        # 转换股票代码格式（适配中国股票）
        if len(stock) == 6 and stock.isdigit():
            # 中国A股代码
            tech_data = akshare_provider.get_stock_technical_data(stock, days=30)
            
            if tech_data is not None and not tech_data.empty:
                current_price = float(tech_data['close'].iloc[-1])
                tech_indicators = {
                    "ma5": float(tech_data['ma5'].iloc[-1]) if 'ma5' in tech_data.columns and pd.notna(tech_data['ma5'].iloc[-1]) else None,
                    "ma20": float(tech_data['ma20'].iloc[-1]) if 'ma20' in tech_data.columns and pd.notna(tech_data['ma20'].iloc[-1]) else None,
                    "rsi": float(tech_data['rsi'].iloc[-1]) if 'rsi' in tech_data.columns and pd.notna(tech_data['rsi'].iloc[-1]) else None,
                    "macd": float(tech_data['macd'].iloc[-1]) if 'macd' in tech_data.columns and pd.notna(tech_data['macd'].iloc[-1]) else None,
                    "volume_ma5": float(tech_data['volume_ma5'].iloc[-1]) if 'volume_ma5' in tech_data.columns and pd.notna(tech_data['volume_ma5'].iloc[-1]) else None,
                    "volume": float(tech_data['volume'].iloc[-1]) if 'volume' in tech_data.columns and pd.notna(tech_data['volume'].iloc[-1]) else None,
                    "high": float(tech_data['high'].iloc[-1]) if 'high' in tech_data.columns and pd.notna(tech_data['high'].iloc[-1]) else None,
                    "low": float(tech_data['low'].iloc[-1]) if 'low' in tech_data.columns and pd.notna(tech_data['low'].iloc[-1]) else None,
                }
                return current_price, tech_indicators
        
        # 回退到Yahoo Finance
        return get_current_price(stock), {}
        
    except Exception as e:
        logging.error(f"Failed to get Chinese stock data for {stock}: {e}")
        return get_current_price(stock), {}

def analyze_technical_indicators(tech_data: Dict) -> Dict[str, str]:
    """分析技术指标并生成信号"""
    signals = {
        "ma_signal": "neutral",
        "rsi_signal": "neutral", 
        "macd_signal": "neutral",
        "volume_signal": "neutral",
        "overall_signal": "neutral"
    }
    
    if not tech_data:
        return signals
    
    try:
        # MA均线分析
        if tech_data.get('ma5') and tech_data.get('ma20'):
            ma5 = tech_data['ma5']
            ma20 = tech_data['ma20']
            current_price = tech_data.get('close', tech_data.get('price', 0))
            
            if current_price > ma5 > ma20:
                signals["ma_signal"] = "bullish"  # 价格在均线上方，看涨
            elif current_price < ma5 < ma20:
                signals["ma_signal"] = "bearish"  # 价格在均线下方，看跌
            elif ma5 > ma20:
                signals["ma_signal"] = "weak_bullish"  # 短期均线在长期上方
            else:
                signals["ma_signal"] = "weak_bearish"  # 短期均线在长期下方
        
        # RSI分析
        if tech_data.get('rsi'):
            rsi = tech_data['rsi']
            if rsi > 70:
                signals["rsi_signal"] = "overbought"  # 超买
            elif rsi < 30:
                signals["rsi_signal"] = "oversold"   # 超卖
            elif rsi > 50:
                signals["rsi_signal"] = "bullish"
            else:
                signals["rsi_signal"] = "bearish"
        
        # MACD分析
        if tech_data.get('macd'):
            macd = tech_data['macd']
            if macd > 0:
                signals["macd_signal"] = "bullish"  # MACD在零轴上方
            else:
                signals["macd_signal"] = "bearish"  # MACD在零轴下方
        
        # 成交量分析
        if tech_data.get('volume') and tech_data.get('volume_ma5'):
            volume = tech_data['volume']
            volume_ma5 = tech_data['volume_ma5']
            if volume > volume_ma5 * 1.5:
                signals["volume_signal"] = "high"  # 成交量放大
            elif volume < volume_ma5 * 0.5:
                signals["volume_signal"] = "low"   # 成交量萎缩
            else:
                signals["volume_signal"] = "normal"
        
        # 综合信号
        bullish_count = sum(1 for signal in [signals["ma_signal"], signals["rsi_signal"], signals["macd_signal"]] 
                          if signal in ["bullish", "weak_bullish"])
        bearish_count = sum(1 for signal in [signals["ma_signal"], signals["rsi_signal"], signals["macd_signal"]] 
                          if signal in ["bearish", "weak_bearish"])
        
        if bullish_count >= 2:
            signals["overall_signal"] = "bullish"
        elif bearish_count >= 2:
            signals["overall_signal"] = "bearish"
        else:
            signals["overall_signal"] = "neutral"
            
    except Exception as e:
        logging.error(f"技术指标分析失败: {e}")
    
    return signals

def calculate_technical_score(tech_data: Dict, signals: Dict) -> float:
    """计算技术指标综合评分 (0-100)"""
    if not tech_data or not signals:
        return 50.0  # 中性分数
    
    score = 50.0  # 基础分数
    
    try:
        # MA信号加分
        ma_signal = signals.get("ma_signal", "neutral")
        if ma_signal == "bullish":
            score += 20
        elif ma_signal == "weak_bullish":
            score += 10
        elif ma_signal == "bearish":
            score -= 20
        elif ma_signal == "weak_bearish":
            score -= 10
        
        # RSI信号加分
        rsi_signal = signals.get("rsi_signal", "neutral")
        if rsi_signal == "oversold":
            score += 15  # 超卖反弹机会
        elif rsi_signal == "bullish":
            score += 10
        elif rsi_signal == "overbought":
            score -= 15  # 超买回调风险
        elif rsi_signal == "bearish":
            score -= 10
        
        # MACD信号加分
        macd_signal = signals.get("macd_signal", "neutral")
        if macd_signal == "bullish":
            score += 10
        elif macd_signal == "bearish":
            score -= 10
        
        # 成交量信号加分
        volume_signal = signals.get("volume_signal", "neutral")
        if volume_signal == "high":
            # 高成交量配合看涨信号加分，配合看跌信号减分
            if signals.get("overall_signal") == "bullish":
                score += 10
            elif signals.get("overall_signal") == "bearish":
                score -= 5
        elif volume_signal == "low":
            score -= 5  # 成交量低迷，减分
        
        # 确保分数在合理范围内
        score = max(0, min(100, score))
        
    except Exception as e:
        logging.error(f"技术分数计算失败: {e}")
        score = 50.0
    
    return score

def store_price(stock: str, price: float, db_path: str = 'ruo.db') -> bool:
    """存储价格到数据库"""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now()
            cursor.execute(
                "INSERT INTO stock_prices (stock, timestamp, price) VALUES (?, ?, ?)", 
                (stock, timestamp, price)
            )
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Failed to store price for {stock}: {e}")
        return False

def get_last_price(stock: str, db_path: str = 'ruo.db') -> Optional[float]:
    """获取上一次价格"""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT price FROM stock_prices WHERE stock=? ORDER BY timestamp DESC LIMIT 1", 
                (stock,)
            )
            result = cursor.fetchone()
            return float(result[0]) if result else None
    except Exception as e:
        logging.error(f"Failed to get last price for {stock}: {e}")
        return None

def calculate_fluctuation(current: float, last: Optional[float]) -> float:
    """计算波动百分比"""
    if last is None or last == 0:
        return 0.0
    return ((current - last) / last) * 100

def initialize_llm(config: Dict) -> Optional[object]:
    """初始化LLM实例"""
    try:
        provider = config.get('llm_provider', 'dashscope').lower()
        model = config.get('quick_think_llm', 'qwen-turbo')
        
        if provider == "openai" or provider == "ollama" or provider == "openrouter":
            return ChatOpenAI(
                model=model, 
                base_url=config.get('backend_url', 'https://api.openai.com/v1'),
                temperature=0.1,
                max_tokens=1000
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model, 
                base_url=config.get('backend_url'),
                temperature=0.1,
                max_tokens=1000
            )
        elif provider == "google":
            google_api_key = os.getenv('GOOGLE_API_KEY')
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=google_api_key,
                temperature=0.1,
                max_tokens=1000
            )
        elif (provider == "dashscope" or provider == "alibaba" or 
              "dashscope" in provider or "阿里百炼" in provider):
            return ChatDashScopeOpenAI(
                model=model,
                temperature=0.1,
                max_tokens=1000
            )
        else:
            logging.error(f"不支持的LLM提供商: {provider}")
            return None
    except Exception as e:
        logging.error(f"初始化LLM失败: {e}")
        return None

def call_ai_agent(stock: str, name: str, current_price: float, last_price: Optional[float], 
                 fluctuation: float, hold_num: int, available: int, cost: float, 
                 tech_data: Dict = None, llm_instance: Optional[object] = None) -> Dict[str, str]:
    """调用AI智能体分析"""
    # 计算收益情况
    profit_loss = ((current_price - cost) / cost * 100) if cost > 0 else 0
    
    # 分析技术指标
    tech_signals = analyze_technical_indicators(tech_data or {})
    tech_score = calculate_technical_score(tech_data or {}, tech_signals)
    
    # 构建技术指标信息字符串
    tech_info = ""
    if tech_data:
        tech_info = f"""
    技术指标分析:
    - MA5: {tech_data.get('ma5', 'N/A'):.2f} | MA20: {tech_data.get('ma20', 'N/A'):.2f} | 均线信号: {tech_signals.get('ma_signal', 'neutral')}
    - RSI: {tech_data.get('rsi', 'N/A'):.2f} | RSI信号: {tech_signals.get('rsi_signal', 'neutral')}
    - MACD: {tech_data.get('macd', 'N/A'):.4f} | MACD信号: {tech_signals.get('macd_signal', 'neutral')}
    - 成交量: {tech_data.get('volume', 'N/A'):,.0f} | 量能5日均: {tech_data.get('volume_ma5', 'N/A'):,.0f} | 量能信号: {tech_signals.get('volume_signal', 'neutral')}
    - 最高: {tech_data.get('high', 'N/A'):.2f} | 最低: {tech_data.get('low', 'N/A'):.2f}
    - 综合技术信号: {tech_signals.get('overall_signal', 'neutral')}
    - 技术评分: {tech_score:.1f}/100
    """
    
    prompt = f"""
    作为专业的股票分析师，请基于以下信息进行综合分析：
    
    股票基本信息:
    - 股票代码: {stock}
    - 股票名称: {name}
    - 上次价格: {last_price}
    - 当前价格: {current_price}
    - 价格波动: {fluctuation:.2f}%
    
    持仓情况:
    - 持仓数量: {hold_num}股  
    - 可用数量: {available}股
    - 成本价格: {cost:.2f}
    - 盈亏情况: {profit_loss:+.2f}%
    {tech_info}
    请综合考虑以下因素进行分析：
    1. 价格波动幅度和方向
    2. 技术指标的信号强度
    3. 成交量变化情况  
    4. 当前持仓盈亏状态
    5. 风险控制考虑
    
    请提供明确的操作建议：'Buy'（买入）、'Sell'（卖出）或'Hold'（持有）。
    请提供简洁但有说服力的分析理由。
    输出JSON格式: {{"action": "Buy/Sell/Hold", "reason": "分析理由", "confidence": "置信度0-100", "technical_score": "{tech_score:.1f}"}}
    """
    
    # 如果有LLM实例，使用AI分析
    if llm_instance:
        try:
            response = llm_instance.invoke(prompt)
            ai_text = response.content if hasattr(response, 'content') else str(response)
            
            # 尝试解析JSON响应
            import re
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                try:
                    ai_response = json.loads(json_match.group())
                    return {
                        "action": ai_response.get("action", "Hold"),
                        "reason": ai_response.get("reason", "AI分析"),
                        "confidence": str(ai_response.get("confidence", 50)),
                        "technical_score": str(ai_response.get("technical_score", tech_score))
                    }
                except json.JSONDecodeError:
                    pass
                    
            # 如果JSON解析失败，基于AI文本内容进行简单判断
            ai_text_lower = ai_text.lower()
            if 'buy' in ai_text_lower or '买入' in ai_text_lower:
                action = "Buy"
            elif 'sell' in ai_text_lower or '卖出' in ai_text_lower:
                action = "Sell"
            else:
                action = "Hold"
                
            return {
                "action": action,
                "reason": ai_text[:150] + "..." if len(ai_text) > 150 else ai_text,
                "confidence": "70",
                "technical_score": str(tech_score)
            }
            
        except Exception as e:
            logging.error(f"AI分析失败: {e}")
    
    # 回退到基于数值和技术指标的简单规则
    default_action = "Hold"  # 默认持有
    reason_parts = [f"价格波动{fluctuation:.2f}%，当前盈亏{profit_loss:.2f}%"]
    
    # 基于技术指标调整建议
    overall_signal = tech_signals.get("overall_signal", "neutral")
    if overall_signal == "bullish" and tech_score > 70:
        if profit_loss < -10:  # 亟损较大时补仓
            default_action = "Buy"
            reason_parts.append("技术指标看涨，建议补仓")
        else:
            default_action = "Hold"
            reason_parts.append("技术指标看涨，持续持有")
    elif overall_signal == "bearish" and tech_score < 30:
        if profit_loss > 5:  # 有盈利时卖出
            default_action = "Sell" 
            reason_parts.append("技术指标看跌，建议获利了结")
        else:
            default_action = "Hold"
            reason_parts.append("技术指标看跌，谨慎持有")
    
    # 波动幅度判断
    if abs(fluctuation) > 10:
        if fluctuation < -10:  # 大幅下跌
            if profit_loss > 5 and overall_signal != "bullish":
                default_action = "Sell"
                reason_parts.append("大幅下跌，建议止盈")
        else:  # 大幅上涨
            if overall_signal == "bearish" and profit_loss > 15:
                default_action = "Sell"
                reason_parts.append("大幅上涨但技术看跌，建议减仓")
    
    return {
        "action": default_action,
        "reason": ", ".join(reason_parts),
        "confidence": str(int(50 + abs(tech_score - 50) * 0.5)),  # 基于技术评分调整置信度
        "technical_score": str(tech_score)
    }

def monitor_stocks(config: Dict = None, llm_instance: Optional[object] = None):
    """定时任务：监控所有股票"""
    if config is None:
        config = DEFAULT_CONFIG
        
    try:
        stocks = get_portfolio_stocks(config.get('db_path', 'ruo.db'))
        if not stocks:
            logging.warning("没有需要监控的股票")
            return
        
        logging.info(f"开始监控 {len(stocks)} 只股票")
        
        # 初始化AKShare提供器（用于中国股票）
        akshare_provider = AKShareProvider()
        
        for stock, name, hold_num, available, cost in stocks:
            try:
                # 获取价格和技术指标
                current_price, tech_data = get_chinese_stock_price_and_tech(stock, akshare_provider)
                
                if current_price is None:
                    logging.warning(f"无法获取 {stock}({name}) 的当前价格")
                    continue
                
                # 存储当前价格
                if not store_price(stock, current_price, config.get('db_path', 'ruo.db')):
                    logging.error(f"存储 {stock} 价格失败")
                    continue
                
                last_price = get_last_price(stock, config.get('db_path', 'ruo.db'))
                
                if last_price is None:
                    logging.info(f"初始价格记录 {stock}({name}): {current_price}")
                    continue
                
                fluctuation = calculate_fluctuation(current_price, last_price)
                profit_loss = ((current_price - cost) / cost * 100) if cost > 0 else 0
                
                # 添加技术指标信息到日志
                tech_info = ""
                if tech_data:
                    tech_signals = analyze_technical_indicators(tech_data)
                    tech_score = calculate_technical_score(tech_data, tech_signals)
                    tech_info = f" | 技术评分: {tech_score:.1f} | 信号: {tech_signals.get('overall_signal', 'neutral')}"
                
                logging.info(
                    f"{stock}({name}) - 当前: {current_price:.2f}, "
                    f"波动: {fluctuation:+.2f}%, 持仓: {hold_num}, 盈亏: {profit_loss:+.2f}%{tech_info}"
                )
                
                # 触发AI分析的条件
                if abs(fluctuation) >= config.get('fluctuation_threshold', 5.0):
                    ai_response = call_ai_agent(
                        stock, name, current_price, last_price, 
                        fluctuation, hold_num, available, cost, tech_data, llm_instance
                    )
                    
                    logging.warning(
                        f"🤖 AI建议 {stock}({name}): {ai_response['action']} - "
                        f"{ai_response['reason']} (置信度: {ai_response.get('confidence', 'N/A')}% | "
                        f"技术评分: {ai_response.get('technical_score', 'N/A')})"
                    )
                    
                    # 发送通知
                    if config.get('enable_notifications', True):
                        send_notification(stock, name, ai_response, current_price, fluctuation)
                        
            except Exception as e:
                logging.error(f"监控股票 {stock} 时发生错误: {e}")
                continue
                
    except Exception as e:
        logging.error(f"股票监控任务执行失败: {e}")


def send_notification(stock: str, name: str, ai_response: Dict[str, str], 
                     current_price: float, fluctuation: float):
    """发送通知（邮件、微信等）"""
    # TODO: 实现通知功能
    message = (
        f"📈 股票监控预警\n"
        f"股票: {stock}({name})\n"
        f"当前价格: {current_price:.2f}\n"
        f"波动幅度: {fluctuation:+.2f}%\n"
        f"AI建议: {ai_response['action']}\n"
        f"理由: {ai_response['reason']}\n"
        f"置信度: {ai_response.get('confidence', 'N/A')}%\n"
        f"技术评分: {ai_response.get('technical_score', 'N/A')}"
    )
    logging.info(f"📢 通知消息: {message}")

def load_config(config_path: str = 'config/stock_monitor.json') -> Dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**DEFAULT_CONFIG, **config}
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict, config_path: str = 'config/stock_monitor.json'):
    """保存配置文件"""
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logging.info(f"配置已保存到 {config_path}")
    except Exception as e:
        logging.error(f"保存配置文件失败: {e}")

def main():
    """主函数"""
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 初始化数据库
    init_database()
    
    # 加载配置
    config = load_config()
    
    logging.info("启动股票监控系统")
    logging.info(f"配置: {config}")
    
    # 初始化LLM
    llm_instance = initialize_llm(config)
    if llm_instance:
        logging.info(f"LLM初始化成功: {config.get('llm_provider')} - {config.get('quick_think_llm')}")
    else:
        logging.warning("LLM初始化失败，将使用简单规则引擎")
    
    # 初始化定时器
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        monitor_stocks, 
        'interval', 
        seconds=config.get('monitor_interval', 300),
        args=[config, llm_instance],
        id='stock_monitor'
    )
    
    try:
        scheduler.start()
        logging.info(f"股票监控已启动，监控间隔: {config.get('monitor_interval', 300)}秒")
        
        # 立即执行一次监控
        monitor_stocks(config, llm_instance)
        
        # 运行系统（阻塞主线程）
        input("按 Enter 键退出...\n")
        
    except KeyboardInterrupt:
        logging.info("收到中断信号，正在关闭系统...")
    finally:
        scheduler.shutdown()
        logging.info("股票监控系统已关闭")

if __name__ == "__main__":
    main()
