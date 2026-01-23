"""
短线龙头助手分析工具

包含龙虎榜分析、候选股票分析、风险收益计算等工具函数
"""

import json
from pathlib import Path
from langchain.tools import tool


@tool
def analyze_lhb_data(lhb_data_json: str) -> str:
    """分析整体龙虎榜数据，识别市场主力资金动向。输入：龙虎榜数据的JSON字符串。用于了解整体市场情况。"""
    try:
        lhb_data = json.loads(lhb_data_json) if isinstance(lhb_data_json, str) else lhb_data_json

        if not lhb_data:
            return "龙虎榜数据为空，无法分析主力资金动向"

        analysis = []
        analysis.append(f"📊 龙虎榜数据分析（共{len(lhb_data)}条记录）：")

        # 分析净买入金额排名
        net_buy_stocks = []
        for item in lhb_data[:10]:  # 只分析前10条
            name = item.get('名称', '')
            net_buy = item.get('龙虎榜净买额', 0)
            reason = item.get('上榜原因', '')
            explanation = item.get('解读', '')

            net_buy_stocks.append({
                'name': name,
                'net_buy': net_buy,
                'reason': reason,
                'explanation': explanation
            })

        # 按净买入金额排序
        net_buy_stocks.sort(key=lambda x: x['net_buy'], reverse=True)

        analysis.append("\n🔥 主力资金净买入TOP5：")
        for i, stock in enumerate(net_buy_stocks[:5]):
            if stock['net_buy'] > 0:
                analysis.append(f"{i+1}. {stock['name']}: +{stock['net_buy']/10000:.0f}万元 ({stock['explanation']})")

        analysis.append("\n📉 主力资金净卖出TOP3：")
        negative_stocks = [s for s in net_buy_stocks if s['net_buy'] < 0]
        for i, stock in enumerate(negative_stocks[:3]):
            analysis.append(f"{i+1}. {stock['name']}: {stock['net_buy']/10000:.0f}万元 ({stock['explanation']})")

        return "\n".join(analysis)

    except Exception as e:
        return f"龙虎榜数据分析失败: {str(e)}"


@tool
def analyze_candidate_stocks(candidates_json: str) -> str:
    """分析候选股票池，筛选连板股、高换手率股票和强势板块。输入：候选股票数据的JSON字符串。这应该是你的第一步分析。"""
    try:
        candidates = json.loads(candidates_json) if isinstance(candidates_json, str) else candidates_json

        if not candidates:
            return "候选股票池为空"

        analysis = []
        analysis.append(f"🎯 候选股票分析（共{len(candidates)}只）：")

        # 按连板数排序
        lianban_stocks = [c for c in candidates if c.get('is_lianban', False)]
        analysis.append(f"\n🚀 连板股（{len(lianban_stocks)}只）：")

        lianban_stocks.sort(key=lambda x: x.get('turnover_rate', 0), reverse=True)
        for i, stock in enumerate(lianban_stocks[:5]):
            analysis.append(f"{i+1}. {stock['name']}({stock['code']}): 换手率{stock.get('turnover_rate', 0):.1f}%, 行业:{stock.get('concept', '')}")

        # 高换手率股票
        high_turnover = [c for c in candidates if c.get('turnover_rate', 0) > 10]
        analysis.append(f"\n💫 高换手率股票（>10%, 共{len(high_turnover)}只）：")

        high_turnover.sort(key=lambda x: x.get('turnover_rate', 0), reverse=True)
        for i, stock in enumerate(high_turnover[:5]):
            analysis.append(f"{i+1}. {stock['name']}({stock['code']}): {stock.get('turnover_rate', 0):.1f}%")

        # 行业分布
        industries = {}
        for stock in candidates:
            industry = stock.get('concept', '未知')
            industries[industry] = industries.get(industry, 0) + 1

        analysis.append(f"\n🏭 行业分布：")
        sorted_industries = sorted(industries.items(), key=lambda x: x[1], reverse=True)
        for industry, count in sorted_industries[:5]:
            analysis.append(f"- {industry}: {count}只")

        return "\n".join(analysis)

    except Exception as e:
        return f"候选股票分析失败: {str(e)}"


@tool
def get_stock_lhb_data(stock_info_json: str, lhb_data_list: str = None) -> str:
    """获取特定股票的龙虎榜数据

    参数格式:
    - stock_info_json: JSON字符串，包含股票代码和名称，例如: '{"code": "000001", "name": "平安银行"}'
    - lhb_data_list: (可选) 全局龙虎榜数据的JSON字符串，如果提供则使用此数据，否则尝试从缓存加载
    """
    try:
        if isinstance(stock_info_json, str):
            stock_info = json.loads(stock_info_json)
        else:
            stock_info = stock_info_json

        code = stock_info.get('code', '')
        name = stock_info.get('name', '')

        if not code or not name:
            return f"❌ 股票信息不完整: {stock_info}"

        # 获取龙虎榜数据
        lhb_data = []
        if lhb_data_list:
            # 如果传入了lhb_data_list，使用它
            if isinstance(lhb_data_list, str):
                lhb_data = json.loads(lhb_data_list)
            else:
                lhb_data = lhb_data_list
        else:
            # 尝试从缓存文件加载（避免在prompt中传递大量数据）
            try:
                cache_dir = Path("cache/daily_research")
                # 查找最新日期的缓存文件
                if cache_dir.exists():
                    subdirs = sorted([d for d in cache_dir.iterdir() if d.is_dir()], reverse=True)
                    if subdirs:
                        latest_dir = subdirs[0]
                        state_file = latest_dir / "state.json"
                        if state_file.exists():
                            with open(state_file, 'r', encoding='utf-8') as f:
                                cached_state = json.load(f)
                                lhb_data = cached_state.get('lhb_data', [])
            except Exception:
                pass

            # 如果缓存加载失败，尝试从全局变量获取（向后兼容）
            if not lhb_data:
                lhb_data = getattr(get_stock_lhb_data, 'lhb_data', [])

        # 查找该股票的龙虎榜记录
        stock_lhb_records = []
        for record in lhb_data:
            if (record.get('代码') == code or
                record.get('名称') == name or
                name in record.get('名称', '')):
                stock_lhb_records.append(record)

        if not stock_lhb_records:
            return f"⚠️ {name}({code}) 未上龙虎榜"

        # 分析该股票的龙虎榜数据
        analysis = []
        analysis.append(f"🎯 {name}({code}) 龙虎榜分析：")

        for i, record in enumerate(stock_lhb_records):
            net_buy = record.get('龙虎榜净买额', 0)
            buy_amount = record.get('龙虎榜买入额', 0)
            sell_amount = record.get('龙虎榜卖出额', 0)
            reason = record.get('上榜原因', '')
            explanation = record.get('解读', '')

            analysis.append(f"\n📊 记录{i+1}:")
            analysis.append(f"- 上榜原因: {reason}")
            analysis.append(f"- 净买入: {net_buy/10000:.0f}万元")
            analysis.append(f"- 买入额: {buy_amount/10000:.0f}万元")
            analysis.append(f"- 卖出额: {sell_amount/10000:.0f}万元")
            analysis.append(f"- 市场解读: {explanation}")

            # 判断主力资金态度
            if net_buy > 0:
                attitude = "看多" if net_buy > buy_amount * 0.3 else "温和看多"
            elif net_buy < 0:
                attitude = "看空" if abs(net_buy) > sell_amount * 0.3 else "温和看空"
            else:
                attitude = "中性"
            analysis.append(f"- 主力态度: {attitude}")

        return "\n".join(analysis)

    except Exception as e:
        return f"获取龙虎榜数据失败: {str(e)}"


@tool
def calculate_risk_reward(stock_data_json: str) -> str:
    """计算风险收益比和买卖点，包括止损价和目标价

    参数格式: JSON字符串，包含股票基本信息
    例如: '{"code": "000001", "name": "平安银行", "turnover_rate": 5.2, "pe": 6.5, "current_price": 10.5}'

    返回格式: JSON字符串，包含止损价、目标价和风险收益比
    """
    try:
        if isinstance(stock_data_json, str):
            stock_data = json.loads(stock_data_json)
        else:
            # 如果传入的不是字符串，尝试直接使用
            stock_data = stock_data_json

        name = stock_data.get('name', '未知股票')
        code = stock_data.get('code', '')
        current_price = float(stock_data.get('current_price', 0))

        # 如果没有价格信息，返回错误
        if current_price <= 0:
            return json.dumps({
                "code": code,
                "name": name,
                "stop_loss": 0,
                "take_profit": 0,
                "risk_reward_ratio": 0,
                "error": "缺少价格信息，无法计算止损价和目标价"
            }, ensure_ascii=False)

        # 基于换手率和PE估算风险等级
        turnover = float(stock_data.get('turnover_rate', 0))
        pe = stock_data.get('pe')

        if turnover > 15:
            risk_level = "高风险"
            risk_score = 3
            # 高风险：止损幅度更大（-8%），目标价更保守（+10%）
            stop_loss_pct = -0.08
            take_profit_pct = 0.10
        elif turnover > 8:
            risk_level = "中风险"
            risk_score = 2
            # 中风险：止损-5%，目标+15%
            stop_loss_pct = -0.05
            take_profit_pct = 0.15
        else:
            risk_level = "低风险"
            risk_score = 1
            # 低风险：止损-3%，目标+20%
            stop_loss_pct = -0.03
            take_profit_pct = 0.20

        # 根据PE调整目标价
        if pe and pe > 0:
            if pe > 100:
                valuation = "高估"
                val_score = 3
                # 高估值：降低目标价
                take_profit_pct *= 0.7
            elif pe > 30:
                valuation = "合理"
                val_score = 2
                # 合理估值：保持目标价
            else:
                valuation = "低估"
                val_score = 1
                # 低估值：提高目标价
                take_profit_pct *= 1.2
        else:
            valuation = "无法评估"
            val_score = 2

        # 计算止损价和目标价
        stop_loss = round(current_price * (1 + stop_loss_pct), 2)
        take_profit = round(current_price * (1 + take_profit_pct), 2)

        # 计算风险收益比
        risk = current_price - stop_loss
        reward = take_profit - current_price
        risk_reward_ratio = round(reward / risk, 2) if risk > 0 else 0

        # 返回JSON格式的结果
        result = {
            "code": code,
            "name": name,
            "current_price": current_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward_ratio": risk_reward_ratio,
            "risk_level": risk_level,
            "valuation": valuation,
            "analysis": f"风险等级: {risk_level}, 估值: {valuation}, 换手率: {turnover:.1f}%"
        }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "error": f"风险收益分析失败: {str(e)}",
            "stop_loss": 0,
            "take_profit": 0,
            "risk_reward_ratio": 0
        }, ensure_ascii=False)