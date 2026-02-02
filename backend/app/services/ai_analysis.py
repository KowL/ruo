"""
AI 分析服务 - AI Analysis Service
MVP v0.1

功能：
- F-06: LLM 情感打分
- 调用 LLM 分析新闻
- 生成一句话摘要
- 判断情感倾向(利好/中性/利空)
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
import logging
import json
import os
from dotenv import load_dotenv

from app.models.news import StockNews, NewsAnalysis

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


class AIAnalysisService:
    """AI 分析服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_client = None
        self.model_name = None
        self._init_llm()

    def _init_llm(self):
        """初始化 LLM 客户端"""
        try:
            # 重新加载环境变量确保获取最新配置
            load_dotenv(override=True)

            # 优先级顺序: ARK(火山方舟) > DeepSeek > DASHSCOPE(阿里百炼) > OpenAI
            api_key = None
            base_url = None
            model_name = None

            # 获取所有可能的API配置
            ark_key = os.getenv('ARK_API_KEY', '')
            deepseek_key = os.getenv('DEEPSEEK_API_KEY', '')
            dashscope_key = os.getenv('DASHSCOPE_API_KEY', '')
            openai_key = os.getenv('OPENAI_API_KEY', '')

            logger.info(f"检测到的API配置: ARK={bool(ark_key and ark_key != 'your_ark_api_key_here')}, "
                       f"DeepSeek={bool(deepseek_key and deepseek_key != 'your_deepseek_api_key_here')}, "
                       f"DashScope={bool(dashscope_key and dashscope_key != 'your_dashscope_api_key_here')}, "
                       f"OpenAI={bool(openai_key and openai_key != 'your_openai_api_key_here')}")

            # 方式1: 尝试火山方舟 ARK (使用DeepSeek-V3模型)
            if ark_key and ark_key != 'your_ark_api_key_here':
                api_key = ark_key
                base_url = 'https://ark.cn-beijing.volces.com/api/v3'
                model_name = 'deepseek-v3-2-251201'
                logger.info("使用火山方舟 DeepSeek-V3 API")

            # 方式2: 尝试 DeepSeek 官方
            elif deepseek_key and deepseek_key != 'your_deepseek_api_key_here':
                api_key = deepseek_key
                base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
                model_name = 'deepseek-chat'
                logger.info("使用 DeepSeek 官方 API")

            # 方式3: 尝试阿里百炼 (通过OpenAI兼容接口)
            elif dashscope_key and dashscope_key != 'your_dashscope_api_key_here':
                api_key = dashscope_key
                base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
                model_name = 'qwen-turbo'  # 使用通义千问
                logger.info("使用阿里百炼(通义千问) API")

            # 方式4: 尝试 OpenAI
            elif openai_key and openai_key != 'your_openai_api_key_here':
                api_key = openai_key
                base_url = 'https://api.openai.com/v1'
                model_name = 'gpt-3.5-turbo'
                logger.info("使用 OpenAI API")

            if not api_key:
                logger.warning("未配置 LLM API Key,AI 分析功能将使用规则模拟")
                # 不返回，使用模拟模式
                self._use_mock_mode = True
                return

            # 使用 OpenAI SDK(兼容多种API)
            from openai import OpenAI

            self.llm_client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            self.model_name = model_name
            self._use_mock_mode = False

            logger.info(f"LLM 客户端初始化成功: {model_name}")

        except Exception as e:
            logger.error(f"LLM 客户端初始化失败: {e}，将使用规则模拟")
            self.llm_client = None
            self.model_name = None
            self._use_mock_mode = True

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
            news = self.db.query(StockNews).filter(StockNews.id == news_id).first()

            if not news:
                raise ValueError(f"新闻不存在: ID={news_id}")

            # 2. 检查是否已分析
            existing_analysis = self.db.query(NewsAnalysis).filter(
                NewsAnalysis.news_id == news_id
            ).first()

            if existing_analysis:
                logger.info(f"新闻已分析过,跳过: ID={news_id}")
                return self._analysis_to_dict(existing_analysis)

            # 3. 调用 LLM 分析 (或使用规则模拟)
            if self._use_mock_mode or not self.llm_client:
                logger.info(f"使用规则模拟进行分析: ID={news_id}")
                analysis_result = self._mock_analyze(
                    stock_code=news.stock_code,
                    title=news.title,
                    content=news.raw_content or news.title
                )
            else:
                analysis_result = self._call_llm(
                    stock_code=news.stock_code,
                    title=news.title,
                    content=news.raw_content or news.title
                )

            # 4. 保存分析结果
            analysis = NewsAnalysis(
                news_id=news_id,
                ai_summary=analysis_result['ai_summary'],
                sentiment_label=analysis_result['sentiment_label'],
                sentiment_score=analysis_result['sentiment_score'],
                llm_model=self.model_name or 'unknown'
            )

            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)

            logger.info(f"新闻分析成功: ID={news_id}, 情感={analysis_result['sentiment_label']}")
            return self._analysis_to_dict(analysis)

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
            unanalyzed_news = self.db.query(StockNews).outerjoin(
                NewsAnalysis, StockNews.id == NewsAnalysis.news_id
            ).filter(
                StockNews.stock_code == symbol,
                NewsAnalysis.id.is_(None)  # 没有分析记录
            ).order_by(StockNews.publish_time.desc()).limit(limit).all()

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
            response = self.llm_client.chat.completions.create(
                model=self.model_name or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一位专业的股票分析师,擅长分析新闻对股价的影响。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )

            # 解析响应
            content = response.choices[0].message.content.strip()

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

    def _mock_analyze(self, stock_code: str, title: str, content: str) -> Dict:
        """
        规则模拟分析 (当LLM不可用时)

        Args:
            stock_code: 股票代码
            title: 新闻标题
            content: 新闻内容

        Returns:
            分析结果
        """
        # 简单的关键词规则
        positive_keywords = ['增长', '上涨', '利好', '超预期', '盈利', '突破', '创新高', '回购', '分红', '业绩']
        negative_keywords = ['下跌', '利空', '亏损', '风险', '下调', '减持', '诉讼', '处罚', '暴跌']

        text = (title + ' ' + content).lower()

        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)

        # 判断情感
        if positive_count > negative_count:
            if positive_count >= 3:
                sentiment_label = '利好'
                sentiment_score = 4.5
            else:
                sentiment_label = '利好'
                sentiment_score = 4.0
        elif negative_count > positive_count:
            if negative_count >= 3:
                sentiment_label = '利空'
                sentiment_score = 1.5
            else:
                sentiment_label = '利空'
                sentiment_score = 2.0
        else:
            sentiment_label = '中性'
            sentiment_score = 3.0

        # 生成摘要（取标题前50字）
        ai_summary = title[:50] if len(title) <= 50 else title[:47] + '...'

        return {
            'ai_summary': ai_summary,
            'sentiment_label': sentiment_label,
            'sentiment_score': sentiment_score
        }

    def _analysis_to_dict(self, analysis: NewsAnalysis) -> Dict:
        """转换分析结果为字典"""
        return {
            'id': analysis.id,
            'newsId': analysis.news_id,
            'aiSummary': analysis.ai_summary,
            'sentimentLabel': analysis.sentiment_label,
            'sentimentScore': analysis.sentiment_score,
            'llmModel': analysis.llm_model,
            'createdAt': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S') if analysis.created_at else None
        }
