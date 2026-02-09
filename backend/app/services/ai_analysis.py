"""
AI 分析服务 - AI Analysis Service
MVP v0.1

功能：
- F-06: LLM 情感打分
- 调用 LLM 分析新闻
- 生成一句话摘要
- 判断情感倾向(利好/中性/利空)
"""
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
import logging
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import func
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.news import News
from app.models.stock import AnalysisReport
from app.models.portfolio import Portfolio
from app.services.market_data import get_market_data_service
from app.core.llm_factory import LLMFactory

# 确保加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


# LLM 提示词模板
SENTIMENT_ANALYSIS_PROMPT = """你是一位专业的股票分析师。请分析以下股票新闻,并给出专业判断。

股票代码:{stock_code}
新闻标题:{title}
新闻内容:{content}

请严格按照 JSON 格式输出分析结果(不要包含其他文字):
{{
  "ai_summary": "用一句话总结这条新闻的核心内容(不超过50字)",
  "sentiment_label": "利好 或 中性 或 利空",
  "sentiment_score": 1到5的星级评分(1=重大利空,2=利空,3=中性,4=利好,5=重大利好)
}}

注意:
1. ai_summary 要简洁明了,突出关键信息
2. sentiment_label 只能是"利好"、"中性"、"利空"三选一
3. sentiment_score 必须是 1-5 的整数
"""

KLINE_ANALYSIS_PROMPT = """你是一位精通在A股市场的技术面分析大师。请根据提供的股票K线数据（日线），进行专业的技术分析。

股票代码: {symbol}
数据包含: 日期, 开盘, 最高, 最低, 收盘, 成交量, 涨跌幅

最近 {days} 个交易日数据如下:
{kline_data}

当前用户的持仓情况（可选参考）：
{portfolio_info}

请基于以上数据，严格按照以下 JSON 格式输出分析报告（不要包含 Markdown 代码块标记，只输出纯 JSON）：

{{
    "summary": "简短的一句话行情总结（50字以内）",
    "trend": "当前趋势（如：上升趋势、下降趋势、震荡整理、底部反弹等）",
    "support_resistance": {{
        "support": "预计支撑位价格（数值）",
        "resistance": "预计压力位价格（数值）",
        "analysis": "关于支撑位和压力位的简要说明"
    }},
    "technical_pattern": "识别出的技术形态（如：金叉、死叉、多头排列、底背离、双底等，如果没有明显形态则填'无明显形态'）",
    "signals": [
        "识别出的关键信号1",
        "识别出的关键信号2"
    ],
    "recommendation": "买入 / 增持 / 持有 / 减持 / 卖出 （五选一）",
    "confidence": 0.0到1.0之间的置信度数值,
    "suggestion": "针对短线操作的具体建议（100字以内）"
}}

注意：
1. 分析要客观、严谨，基于数据。
2. 支撑位和压力位要给出具体价格参考。
3. recommendation 必须是指定枚举值之一。
"""


class AIAnalysisService:
    """AI 分析服务类"""

    def __init__(self, db: Session):
        self.db = db
        try:
            self.llm = LLMFactory.get_instance()
            self.model_name = getattr(self.llm, "model_name", "unknown")
        except Exception as e:
            logger.error(f"LLMFactory 初始化失败: {e}")
            self.llm = None
            self.model_name = None

    def analyze_news(self, news_id: int) -> Optional[Dict]:
        """
        分析单条新闻

        Args:
            news_id: 新闻ID

        Returns:
            分析结果
        """
        try:
            # 1. 查询新闻
            news = self.db.query(News).filter(News.id == news_id).first()

            if not news:
                raise ValueError(f"新闻不存在: ID={news_id}")

            # 2. 检查是否已分析
            if news.ai_analysis:
                logger.info(f"新闻已分析过,跳过: ID={news_id}")
                try:
                    return json.loads(news.ai_analysis)
                except:
                    pass

            # 3. 调用 LLM 分析
            if not self.llm:
                 raise ValueError("LLM 客户端未初始化，无法进行分析")
                 
            # 需要从 relation_stock 中获取股票代码，或者如果是一般新闻则可能没有特定代码
            # News 模型没有 stock_code 字段，只有 relation_stock (text)
            stock_code = "UNKNOWN"
            if news.relation_stock:
                stock_code = news.relation_stock.split(',')[0]
                
            analysis_result = self._call_llm(
                stock_code=stock_code,
                title=news.title,
                content=news.content or news.title
            )

            # 4. 保存分析结果
            # 将结果保存到 ai_analysis 字段 (JSON 字符串)
            analysis_json = json.dumps(analysis_result, ensure_ascii=False)
            news.ai_analysis = analysis_json
            
            self.db.commit()
            self.db.refresh(news)

            logger.info(f"新闻分析成功: ID={news_id}, 情感={analysis_result['sentiment_label']}")
            return analysis_result

        except Exception as e:
            self.db.rollback()
            logger.error(f"分析新闻失败: ID={news_id}, 错误: {e}")
            return None

    def batch_analyze_news(self, symbol: str, limit: int = 10) -> Dict:
        """
        批量分析股票的未分析新闻

        Args:
            symbol: 股票代码
            limit: 最多分析 N 条

        Returns:
            {
                "analyzed": 分析成功数量,
                "failed": 分析失败数量
            }
        """
        try:
            # 查询未分析的新闻
            # News.relation_stock 包含 symbol
            unanalyzed_news = self.db.query(News).filter(
                News.relation_stock.like(f"%{symbol}%"),
                News.ai_analysis.is_(None)
            ).order_by(News.publish_time.desc()).limit(limit).all()

            analyzed_count = 0
            failed_count = 0

            for news in unanalyzed_news:
                result = self.analyze_news(news.id)
                if result:
                    analyzed_count += 1
                else:
                    failed_count += 1

            logger.info(f"批量分析完成: {symbol}, 成功={analyzed_count}, 失败={failed_count}")

            return {
                "analyzed": analyzed_count,
                "failed": failed_count
            }

        except Exception as e:
            logger.error(f"批量分析新闻失败: {symbol}, 错误: {e}")
            return {"analyzed": 0, "failed": 0}

    def analyze_kline(self, symbol: str, days: int = 20) -> Dict:
        """
        K线 AI 分析

        Args:
            symbol: 股票代码
            days: 分析最近 N 天的数据

        Returns:
            分析结果字典
        """
        try:
            logger.info(f"开始 K线 AI 分析: {symbol}, days={days}")
            
            # 1. 获取 K 线数据
            market_service = get_market_data_service()
            kline_data = market_service.get_kline_data(symbol, period='daily', limit=days)
            
            if not kline_data:
                raise ValueError(f"未获取到K线数据: {symbol}")
            
            # 格式化数据供 LLM 使用
            kline_str_list = []
            for k in kline_data:
                # 日期, 开, 高, 低, 收, 量, 幅
                line = f"{k['date']}: 开{k['open']}, 高{k['high']}, 低{k['low']}, 收{k['close']}, 量{k['volume']}, 幅{k['changePct']}%"
                kline_str_list.append(line)
            
            kline_text = "\\n".join(kline_str_list)
            
            # 3. 获取持仓信息 (MVP user_id=1)
            portfolio_info = "用户当前无持仓。"
            try:
                portfolio = self.db.query(Portfolio).filter(
                    Portfolio.user_id == 1,
                    Portfolio.symbol == symbol,
                    Portfolio.is_active == 1
                ).first()
                
                if portfolio:
                    portfolio_info = f"用户持有 {portfolio.quantity} 股，成本价 {portfolio.cost_price}，策略: {portfolio.strategy_tag or '无'}。请结合成本价给出操作建议（如止盈止损）。"
            except Exception as e:
                logger.warning(f"获取持仓信息失败: {e}")

            # 4. 调用 LLM 分析
            prompt = KLINE_ANALYSIS_PROMPT.format(
                symbol=symbol,
                days=days,
                kline_data=kline_text,
                portfolio_info=portfolio_info
            )
            
            if not self.llm:
                 raise ValueError("LLM 客户端未初始化，无法进行分析")

            messages = [
                SystemMessage(content="你是一位专业的股票技术分析师。"),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            
            content = response.content.strip()
            
            # 提取 JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            analysis_result = json.loads(content)
            
            # 3. 保存报告
            today = datetime.now().strftime('%Y-%m-%d')
            report = AnalysisReport(
                symbol=symbol,
                report_date=today,
                report_type='kline_analysis',
                content=self._generate_kline_markdown(symbol, analysis_result),
                data=json.dumps(analysis_result, ensure_ascii=False),
                summary=analysis_result.get('summary', ''),
                recommendation=analysis_result.get('recommendation', '持有'),
                confidence=analysis_result.get('confidence', 0.5)
            )
            
            # 检查当日是否已有报告，若有则更新
            existing = self.db.query(AnalysisReport).filter(
                AnalysisReport.symbol == symbol,
                AnalysisReport.report_date == today,
                AnalysisReport.report_type == 'kline_analysis'
            ).first()
            
            if existing:
                existing.content = report.content
                existing.data = report.data
                existing.summary = report.summary
                existing.recommendation = report.recommendation
                existing.confidence = report.confidence
                existing.created_at = func.now() # Update time
            else:
                self.db.add(report)
            
            self.db.commit()
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"K线分析失败: {symbol}, 错误: {e}")
            self.db.rollback()
            raise

    def _generate_kline_markdown(self, symbol: str, result: Dict) -> str:
        """生成 Markdown 格式报告"""
        return f"""# {symbol} K线技术分析报告

**日期**: {datetime.now().strftime('%Y-%m-%d')}
**评级**: {result.get('recommendation')} (置信度: {result.get('confidence')})

## 摘要
{result.get('summary')}

## 趋势分析
**当前趋势**: {result.get('trend')}

## 关键点位
- **支撑位**: {result.get('support_resistance', {}).get('support')}
- **压力位**: {result.get('support_resistance', {}).get('resistance')}
- **分析**: {result.get('support_resistance', {}).get('analysis')}

## 技术形态
{result.get('technical_pattern')}

## 关键信号
{chr(10).join(['- ' + s for s in result.get('signals', [])])}

## 操作建议
{result.get('suggestion')}

---
*注：本报告由 AI 自动生成，仅供参考，不构成投资建议。*
"""



    def _call_llm(self, stock_code: str, title: str, content: str) -> Dict:
        """
        调用 LLM 进行分析

        Args:
            stock_code: 股票代码
            title: 新闻标题
            content: 新闻内容

        Returns:
            {
                "ai_summary": str,
                "sentiment_label": str,
                "sentiment_score": float
            }
        """
        try:
            # 构建提示词
            prompt = SENTIMENT_ANALYSIS_PROMPT.format(
                stock_code=stock_code,
                title=title,
                content=content[:500]  # 限制长度
            )

            # 调用 LLM
            messages = [
                SystemMessage(content="你是一位专业的股票分析师,擅长分析新闻对股价的影响。"),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            
            # 解析响应
            content = response.content.strip()

            # 提取 JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            result = json.loads(content)

            # 验证结果
            if not all(k in result for k in ['ai_summary', 'sentiment_label', 'sentiment_score']):
                raise ValueError("LLM 返回结果格式不正确")

            # 验证情感标签
            if result['sentiment_label'] not in ['利好', '中性', '利空']:
                result['sentiment_label'] = '中性'

            # 验证分数
            result['sentiment_score'] = float(result['sentiment_score'])
            if not (1 <= result['sentiment_score'] <= 5):
                result['sentiment_score'] = 3.0

            return result

        except json.JSONDecodeError as e:
            logger.error(f"LLM 返回的 JSON 解析失败: {e}, 内容: {content}")
            # 返回默认值
            return {
                "ai_summary": title[:50],
                "sentiment_label": "中性",
                "sentiment_score": 3.0
            }
        except Exception as e:
            logger.error(f"调用 LLM 失败: {e}")
            raise



    # _analysis_to_dict helper is no longer needed as we return dict or None directly
