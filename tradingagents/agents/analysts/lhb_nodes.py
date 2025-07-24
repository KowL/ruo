import akshare as ak
import pandas as pd

def fetch_lhb_data(context=None):
    """
    获取今日龙虎榜数据，并排除ST股票。
    返回：
        DataFrame，已过滤ST股票的龙虎榜数据
    """
    # 获取今日龙虎榜数据
    try:
        lhb_df = ak.stock_lhb_detail_em(date=pd.Timestamp.today().strftime('%Y%m%d'))
    except Exception as e:
        return {"error": f"龙虎榜数据获取失败: {e}"}

    # 排除ST股票
    if '股票简称' in lhb_df.columns:
        lhb_df = lhb_df[~lhb_df['股票简称'].str.contains('ST')]
    elif '名称' in lhb_df.columns:
        lhb_df = lhb_df[~lhb_df['名称'].str.contains('ST')]

    # 可选：重置索引
    lhb_df = lhb_df.reset_index(drop=True)

    # 返回DataFrame或dict，供后续分析节点使用
    return {"lhb_data": lhb_df}

def analyze_lhb_data(context):
    """
    龙虎榜数据多维度分析：
    1. 资金流向分析
    2. 席位动向分析
    3. 历史对比分析
    4. 技术指标分析
    """
    lhb_df = context.get("lhb_data")
    if lhb_df is None or isinstance(lhb_df, dict) and "error" in lhb_df:
        return {"error": "无龙虎榜数据，无法分析"}

    analyzed_list = []
    for idx, row in lhb_df.iterrows():
        code = row.get("股票代码") or row.get("代码")
        name = row.get("股票简称") or row.get("名称")
        # 1. 资金流向分析（示例：主力净买额/净流入）
        net_main_fund = row.get("净买额") or row.get("主力净买额") or 0
        # 2. 席位动向分析（示例：机构买入、游资买入）
        inst_buy = row.get("机构买入") or 0
        hot_money_buy = row.get("游资买入") or 0
        # 3. 历史对比分析（可扩展，暂留空）
        # 4. 技术指标分析（示例：获取近5日K线均线、MACD等）
        try:
            kline = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=None, end_date=None, adjust="qfq")
            kline = kline.tail(20)
            ma5 = kline["收盘"].rolling(window=5).mean().iloc[-1]
            ma20 = kline["收盘"].rolling(window=20).mean().iloc[-1]
            last_close = kline["收盘"].iloc[-1]
            trend = "上升" if last_close > ma5 > ma20 else ("震荡" if abs(ma5-ma20)/ma20<0.01 else "下跌")
        except Exception:
            ma5 = ma20 = last_close = None
            trend = "未知"
        analyzed_list.append({
            "code": code,
            "name": name,
            "net_main_fund": net_main_fund,
            "inst_buy": inst_buy,
            "hot_money_buy": hot_money_buy,
            "trend": trend,
            # "history": ... # 可扩展
        })
    return {"analyzed_data": analyzed_list}

def generate_lhb_suggestion(context):
    """
    根据分析结果生成操作建议。
    规则：
    1. 买入：主力资金净流入显著（>1000万），机构买入高，且趋势上升
    2. 卖出：主力资金净流出（<-1000万），游资抛售高，且趋势下跌
    3. 持有：资金流向中性（-1000万~1000万），趋势未破
    4. 观望：资金流向混乱或趋势未知
    """
    analyzed_list = context.get("analyzed_data", [])
    suggestions = []
    for item in analyzed_list:
        code = item.get("code")
        name = item.get("name")
        net_main_fund = float(item.get("net_main_fund") or 0)
        inst_buy = float(item.get("inst_buy") or 0)
        hot_money_buy = float(item.get("hot_money_buy") or 0)
        trend = item.get("trend")
        # 建议与理由
        if net_main_fund > 10000000 and inst_buy > hot_money_buy and trend == "上升":
            suggestion = "买入"
            reason = f"主力资金净流入显著，机构席位买入占比高，技术指标显示上升趋势"
        elif net_main_fund < -10000000 and hot_money_buy > inst_buy and trend == "下跌":
            suggestion = "卖出"
            reason = f"主力资金净流出，游资抛售明显，技术指标显示下跌趋势"
        elif -10000000 <= net_main_fund <= 10000000 and trend in ["上升", "震荡"]:
            suggestion = "持有"
            reason = f"资金流向中性，趋势未破，建议继续观察"
        else:
            suggestion = "观望"
            reason = f"资金流向混乱或技术指标无明确信号"
        suggestions.append({
            "code": code,
            "name": name,
            "suggestion": suggestion,
            "reason": reason
        })
    return {"suggestions": suggestions}

def output_lhb_result(context):
    """
    输出最终龙虎榜分析结果，包含：
    - 股票代码、名称
    - 操作建议
    - 建议理由
    - 风险提示
    """
    suggestions = context.get("suggestions", [])
    print("\n今日龙虎榜分析与操作建议：")
    for item in suggestions:
        code = item.get("code")
        name = item.get("name")
        suggestion = item.get("suggestion")
        reason = item.get("reason")
        # 风险提示（可根据实际情况扩展）
        risk = "市场有系统性风险，注意仓位控制，警惕个股突发事件。"
        print(f"股票代码: {code}  名称: {name}")
        print(f"操作建议: {suggestion}")
        print(f"建议理由: {reason}")
        print(f"风险提示: {risk}")
        print("-"*40)
    return suggestions 