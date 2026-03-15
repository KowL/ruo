import json
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from sqlalchemy.sql import func
from app.llm_agent.graphs.limit_up_stock_analysis_graph import run_ai_research_analysis
from app.core.database import get_db, SessionLocal
from app.models.stock import AnalysisReport
from app.services.ai_analysis import AIAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter()

class AnalysisRequest(BaseModel):
    date: Optional[str] = None
    force_rerun: bool = False

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None
    cached: bool = False


def _get_existing_report(db: Session, date_str: str, analysis_type: str, symbol: str = "GLOBAL"):
    """
    检查是否存在已有的报告或正在处理的记录
    """
    report_date = datetime.strptime(date_str, "%Y-%m-%d")
    query = db.query(AnalysisReport).filter(
        AnalysisReport.report_date == report_date,
        AnalysisReport.analysis_type == analysis_type
    )
    if symbol:
        query = query.filter(AnalysisReport.symbol == symbol)
    
    existing = query.first()
    return existing, report_date

def background_analysis_task(date: str, force_rerun: bool, report_id: int):
    """
    后台分析任务包装函数
    """
    db = SessionLocal()
    try:
        logger.info(f"🚀 开始后台分析任务: {date}_limit-up")
        run_ai_research_analysis(date=date, force_rerun=force_rerun)
        logger.info(f"✅ 后台分析任务完成: {date}_limit-up")
    except Exception as e:
        logger.error(f"❌ 后台分析任务失败 ({date}_limit-up): {e}")
        try:
            report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
            if report:
                report.status = "failed"
                report.content = f"分析失败: {str(e)}"
                db.commit()
        except:
            pass
    finally:
        db.close()


def background_opening_analysis_task(date: str, force_rerun: bool, report_id: int):
    """
    后台开盘分析任务包装函数
    """
    db = SessionLocal()
    try:
        logger.info(f"🚀 开始后台开盘分析任务: {date}_opening_analysis")
        from app.llm_agent.graphs.opening_analysis_workflow import run_opening_analysis
        run_opening_analysis(date=date, force_rerun=force_rerun)
        logger.info(f"✅ 后台开盘分析任务完成: {date}_opening_analysis")
    except Exception as e:
        logger.error(f"❌ 后台开盘分析任务失败 ({date}_opening_analysis): {e}")
        try:
            report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
            if report:
                report.status = "failed"
                report.content = f"分析失败: {str(e)}"
                db.commit()
        except:
            pass
    finally:
        db.close()

@router.get("/report", response_model=AnalysisResponse)
async def get_analysis_report(
    analysis_type: str,
    date: str,
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    查询指定类型和日期的分析报告
    """
    try:
        # 使用公共方法查询
        report, _ = _get_existing_report(db, date, analysis_type, symbol)
        
        if not report:
            return AnalysisResponse(
                success=False,
                message=f"未找到 {date} 的 {analysis_type} 分析报告",
                cached=False
            )
            
        # 提取数据
        markdown_content = report.content
        raw_data = {}
        if report.data:
            try:
                raw_data = json.loads(report.data)
            except:
                raw_data = {"message": "Could not parse JSON data"}
        
        # 组装返回结果
        result_data = {
            "markdown": markdown_content,
            "data": raw_data,
            "date": date
        }
                
        return AnalysisResponse(
            success=True,
            message="查询成功",
            result=result_data,
            cached=True
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class KlineAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="股票代码")
    force_rerun: bool = False


def background_kline_analysis_task(symbol: str, days: int, force_rerun: bool, report_id: int):
    """
    后台K线分析任务
    """
    db = SessionLocal()
    try:
        logger.info(f"🚀 开始后台K线分析任务: {symbol}")
        
        service = AIAnalysisService(db)
        service.analyze_kline(symbol, days)
            
        logger.info(f"✅ 后台K线分析任务完成: {symbol}")
    except Exception as e:
        logger.error(f"❌ 后台K线分析任务失败 ({symbol}): {e}")
        try:
            report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
            if report:
                report.status = "failed"
                report.content = f"分析失败: {str(e)}"
                db.commit()
        except:
            pass
    finally:
        db.close()


@router.post("/kline", response_model=AnalysisResponse)
async def run_kline_analysis(
    background_tasks: BackgroundTasks,
    request: KlineAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    运行K线 AI 分析（异步模式）
    """
    
    # 2. 检查当日是否已分析或正在分析
    today = datetime.now().strftime('%Y-%m-%d')
    existing, report_date = _get_existing_report(db, today, 'kline_analysis', request.symbol)
    
    if existing:
        if existing.status == "processing":
            return AnalysisResponse(
                success=True,
                message=f"分析进行中，稍后在历史记录中查看",
                cached=False
            )
        if not request.force_rerun:
            return AnalysisResponse(
                success=True,
                message="分析已完成，请查询报告。",
                cached=True
            )
    
    # 3. 创建正在处理的记录（如果不存在或强制重跑）
    if not existing:
        existing = AnalysisReport(
            symbol=request.symbol,
            report_date=report_date,
            analysis_type='kline_analysis',
            analysis_name='K线技术分析',
            status="processing",
            content="",
            summary=f"股票 {request.symbol} K线技术分析中...",
            recommendation="hold"
        )
        db.add(existing)
    else:
        existing.status = "processing"
        existing.content = ""
        existing.summary = f"股票 {request.symbol} K线技术分析中..."
    
    db.commit()
    db.refresh(existing)
    
    # 4. 启动后台任务 - 默认分析90天
    background_tasks.add_task(
        background_kline_analysis_task, 
        request.symbol, 
        90, 
        request.force_rerun,
        existing.id
    )
    
    return AnalysisResponse(
        success=True,
        message=f"已启动 {request.symbol} K线分析，请在历史报告中查看进度",
        result={"report_id": existing.id},
        cached=False
    )


class HistoryItem(BaseModel):
    """历史报告条目"""
    id: int
    report_date: str
    analysis_type: str
    analysis_name: Optional[str] = None
    symbol: str
    summary: Optional[str] = None
    status: str = "completed"
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    created_at: Optional[str] = None

class HistoryListResponse(BaseModel):
    """历史报告列表响应"""
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None
    total: int = 0
    page: int = 1
    page_size: int = 20


@router.get("/history", response_model=HistoryListResponse)
async def get_analysis_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    analysis_type: Optional[str] = Query(None, description="报告类型过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    获取分析报告历史列表（分页）
    """
    try:
        # 构建查询
        query = db.query(AnalysisReport)
        
        # 按报告类型过滤
        if analysis_type and analysis_type != 'all':
            query = query.filter(AnalysisReport.analysis_type == analysis_type)

        # 按日期范围过滤
        if start_date:
            try:
                s_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(AnalysisReport.report_date >= s_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="start_date 格式无效")
        
        if end_date:
            try:
                e_dt = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(AnalysisReport.report_date <= e_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="end_date 格式无效")
        
        # 获取总数
        total = query.count()
        
        # 分页查询，按日期倒序
        offset = (page - 1) * page_size
        reports = query.order_by(desc(AnalysisReport.report_date)).offset(offset).limit(page_size).all()
        
        # 转换为响应格式
        items = []
        for r in reports:
            items.append({
                "id": r.id,
                "report_date": r.report_date.strftime("%Y-%m-%d") if r.report_date else "",
                "analysis_type": r.analysis_type,
                "analysis_name": r.analysis_name,
                "symbol": r.symbol,
                "summary": r.summary or "",
                "status": r.status,
                "recommendation": r.recommendation,
                "confidence": r.confidence,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
            })
        
        return HistoryListResponse(
            success=True,
            message="查询成功",
            result={"items": items},
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{report_id}", response_model=AnalysisResponse)
async def get_history_detail(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    获取历史报告详情
    """
    try:
        report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
        
        if not report:
            return AnalysisResponse(
                success=False,
                message="未找到该报告",
                cached=False
            )
        
        # 提取数据
        markdown_content = report.content
        raw_data = {}
        if report.data:
            try:
                raw_data = json.loads(report.data)
            except:
                raw_data = {"message": "Could not parse JSON data"}
        
        # 确定名称
        analysis_name = report.analysis_name
        if not analysis_name:
            analysis_name = "市场复盘" if report.analysis_type == "limit-up" else "开盘分析"
            if report.analysis_type == "opening_analysis":
                analysis_name = "开盘分析"
            elif report.analysis_type == "kline_analysis":
                analysis_name = "K线分析"
        
        # 组装返回结果
        result_data = {
            "id": report.id,
            "markdown": markdown_content,
            "data": raw_data,
            "date": report.report_date.strftime("%Y-%m-%d") if report.report_date else "",
            "analysis_type": report.analysis_type,
            "analysis_name": analysis_name,
            "symbol": report.symbol,
            "summary": report.summary,
            "recommendation": report.recommendation,
            "confidence": report.confidence
        }
                
        return AnalysisResponse(
            success=True,
            message="查询成功",
            result=result_data,
            cached=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 自定义分析接口
# ========================================

class UnifiedAnalysisRequest(BaseModel):
    """统一分析请求"""
    analysisType: str = Field(..., description="分析类型: limit-up | opening-analysis | prompt")
    analysisName: Optional[str] = Field(default=None, description="分析名称，如'复盘分析'、'开盘分析'、'提示词名称'")
    prompt: Optional[str] = Field(default=None, description="提示词内容（prompt类型时必填）")
    analysisParam: Optional[Dict[str, Any]] = Field(default=None, description="分析参数，如 date")


class UnifiedAnalysisResponse(BaseModel):
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None
    cached: bool = False


@router.post("/start", response_model=UnifiedAnalysisResponse)
async def start_unified_analysis(
    background_tasks: BackgroundTasks,
    request: UnifiedAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    统一分析接口
    
    根据 analysisType 区分分析任务流：
    - limit-up: 复盘分析
    - opening-analysis: 开盘分析
    - prompt: 自定义提示词分析（需要提供 prompt 参数）
    """
    analysis_type = request.analysisType
    analysis_name = request.analysisName
    prompt = request.prompt
    analysis_param = request.analysisParam or {}
    target_date = analysis_param.get("date")
    
    # 如果没有指定日期，使用今天
    if not target_date:
        target_date = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    
    target_date_str = target_date
    
    try:
        # 检查是否有正在处理的记录或已完成记录
        existing, report_date = _get_existing_report(db, target_date_str, analysis_type)
        if existing:
            if existing.status == "processing":
                return UnifiedAnalysisResponse(
                    success=True,
                    message="分析正在执行中，稍后在历史记录查询。",
                    cached=False
                )

        # 创建正在处理的记录
        report = AnalysisReport(
            symbol="GLOBAL",
            report_date=report_date,
            analysis_type=analysis_type,
            analysis_name=analysis_name,
            status="processing",
            content="",
            summary="分析进行中...",
            recommendation="hold"
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        if analysis_type == "limit-up":
            # 启动后台任务
            background_tasks.add_task(background_analysis_task, target_date_str, False, report.id)
            
            return UnifiedAnalysisResponse(
                success=True,
                message="复盘分析已启动，请在历史记录中查看进度",
                result={"report_id": report.id},
                cached=False
            )
            
        elif analysis_type == "opening-analysis":
            # 启动后台任务
            background_tasks.add_task(background_opening_analysis_task, target_date_str, False, report.id)
            
            return UnifiedAnalysisResponse(
                success=True,
                message="开盘分析已启动，请在历史记录中查看进度",
                result={"report_id": report.id},
                cached=False
            )
            
        elif analysis_type == "prompt":
            # 自定义提示词分析
            if not prompt:
                return UnifiedAnalysisResponse(
                    success=False,
                    message="prompt类型分析需要提供 prompt 参数",
                    cached=False
                )
            
            report_id = report.id
            
            # 使用传入的 analysis_name 或默认值
            run_name = analysis_name if analysis_name else "自定义提示词分析"
            
            # 启动后台分析任务
            background_tasks.add_task(run_custom_analysis_task, report_id, prompt, run_name)
            
            return UnifiedAnalysisResponse(
                success=True,
                message="自定义分析已启动，请稍后在历史报告中查看",
                result={"report_id": report_id},
                cached=False
            )
            
        else:
            return UnifiedAnalysisResponse(
                success=False,
                message=f"不支持的分析类型: {analysis_type}，支持的类型: limit-up, opening-analysis, prompt",
                cached=False
            )
            
    except Exception as e:
        logger.error(f"统一分析接口异常: {e}")
        return UnifiedAnalysisResponse(
            success=False,
            message=f"分析任务创建失败: {str(e)}",
            cached=False
        )


def run_custom_analysis_task(report_id: int, prompt: str, analysis_name: str = "自定义提示词分析"):
    """
    后台自定义分析任务
    """
    db = SessionLocal()
    try:
        logger.info(f"🚀 开始提示词分析任务: report_{report_id}, prompt={prompt[:50]}...")
        
        # 获取报告记录
        report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
        if not report:
            logger.error(f"报告不存在: {report_id}")
            return
        
        # 调用 AI 分析服务
        try:
            service = AIAnalysisService(db)
            # 使用通用 LLM 分析 - 这里可以根据 prompt 内容调用不同的分析方法
            # 这里简单处理：调用 LLM 进行通用分析
            from app.core.llm_factory import LLMFactory
            llm = LLMFactory.get_instance()
            
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content="你是一位专业的股票分析师，擅长分析市场数据并给出投资建议。用中文回复。"),
                HumanMessage(content=prompt)
            ]
            response = llm.invoke(messages)
            
            # 解析结果
            content = response.content.strip()
            
            # 提取可能的 JSON 或直接使用文本
            analysis_result = {
                "prompt": prompt,
                "analysis": content,
                "timestamp": datetime.now().isoformat()
            }
            
            # 保存报告
            report.content = content
            report.data = json.dumps(analysis_result, ensure_ascii=False)
            report.summary = content[:200] if content else ""
            report.status = "completed"
            
            # 尝试提取推荐
            if "买入" in content or "增持" in content:
                report.recommendation = "buy"
            elif "卖出" in content or "减持" in content:
                report.recommendation = "sell"
            else:
                report.recommendation = "hold"
            
            # 尝试提取置信度
            if "置信度" in content:
                import re
                match = re.search(r'(\d+\.?\d*)%', content)
                if match:
                    report.confidence = float(match.group(1)) / 100
            
            db.commit()
            logger.info(f"✅ 自定义分析任务完成: report_{report_id}")
            
        except Exception as e:
            logger.error(f"自定义分析失败: {e}")
            report.status = "failed"
            report.content = f"分析失败: {str(e)}"
            db.commit()
            
    except Exception as e:
        logger.error(f"自定义分析任务异常: {e}")
        try:
            report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
            if report:
                report.status = "failed"
                report.content = f"分析失败: {str(e)}"
                db.commit()
        except:
            pass
    finally:
        db.close()
