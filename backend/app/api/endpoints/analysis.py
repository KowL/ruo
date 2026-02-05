import json
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.llm_agent.graphs.limit_up_stock_analysis_graph import run_ai_research_analysis
from app.core.database import get_db
from app.models.stock import AnalysisReport

router = APIRouter()

class AnalysisRequest(BaseModel):
    date: Optional[str] = None
    force_rerun: bool = False

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None
    cached: bool = False

# 用于跟踪正在运行的任务 (Key: {date}_{report_type})
active_tasks = set()

def background_analysis_task(date: str, force_rerun: bool):
    """
    后台分析任务包装函数
    """
    task_key = f"{date}_limit-up"
    try:
        active_tasks.add(task_key)
        print(f"🚀 开始后台分析任务: {task_key}")
        run_ai_research_analysis(date=date, force_rerun=force_rerun)
        print(f"✅ 后台分析任务完成: {task_key}")
    except Exception as e:
        print(f"❌ 后台分析任务失败 ({task_key}): {e}")
    finally:
        active_tasks.discard(task_key)

@router.post("/limit-up", response_model=AnalysisResponse)
async def run_limit_up_analysis(
    background_tasks: BackgroundTasks,
    request: AnalysisRequest = AnalysisRequest(),
    db: Session = Depends(get_db)
):
    """
    运行涨停股分析（异步模式）
    """
    target_date = request.date or datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    task_key = f"{target_date}_limit-up"
    
    # 1. 检查是否已经在运行中
    if task_key in active_tasks:
        return AnalysisResponse(
            success=True,
            message="分析中，请等待",
            cached=False
        )
    
    # 2. 检查是否已经存在完成的任务
    if not request.force_rerun:
        report_date = datetime.strptime(target_date, "%Y-%m-%d")
        existing = db.query(AnalysisReport).filter(
            AnalysisReport.report_date == report_date,
            AnalysisReport.report_type == "limit-up"
        ).first()
        
        if existing:
            return AnalysisResponse(
                success=True,
                message="分析完成，请查询报告。",
                cached=True
            )
            
    # 3. 启动后台任务
    background_tasks.add_task(background_analysis_task, target_date, request.force_rerun)
    
    
    return AnalysisResponse(
        success=True,
        message="分析中，请等待",
        cached=False
    )

def background_opening_analysis_task(date: str, force_rerun: bool):
    """
    后台开盘分析任务包装函数
    """
    task_key = f"{date}_opening_analysis"
    try:
        active_tasks.add(task_key)
        print(f"🚀 开始后台开盘分析任务: {task_key}")
        from app.llm_agent.graphs.opening_analysis_workflow import run_opening_analysis
        run_opening_analysis(date=date, force_rerun=force_rerun)
        print(f"✅ 后台开盘分析任务完成: {task_key}")
    except Exception as e:
        print(f"❌ 后台开盘分析任务失败 ({task_key}): {e}")
    finally:
        active_tasks.discard(task_key)

@router.post("/opening-analysis", response_model=AnalysisResponse)
async def run_opening_analysis_endpoint(
    background_tasks: BackgroundTasks,
    request: AnalysisRequest = AnalysisRequest(),
    db: Session = Depends(get_db)
):
    """
    运行开盘分析（异步模式）
    """
    target_date = request.date or datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    task_key = f"{target_date}_opening_analysis"
    
    # 1. 检查是否已经在运行中
    if task_key in active_tasks:
        return AnalysisResponse(
            success=True,
            message="开盘分析进行中，请等待",
            cached=False
        )
    
    # 2. 检查是否已经存在完成的任务
    if not request.force_rerun:
        report_date = datetime.strptime(target_date, "%Y-%m-%d")
        existing = db.query(AnalysisReport).filter(
            AnalysisReport.report_date == report_date,
            AnalysisReport.report_type == "opening_analysis"
        ).first()
        
        if existing:
            return AnalysisResponse(
                success=True,
                message="分析完成，请查询报告。",
                cached=True
            )
            
    # 3. 启动后台任务
    background_tasks.add_task(background_opening_analysis_task, target_date, request.force_rerun)
    
    return AnalysisResponse(
        success=True,
        message="开盘分析已启动，请等待",
        cached=False
    )

@router.get("/report", response_model=AnalysisResponse)
async def get_analysis_report(
    report_type: str,
    date: str,
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    查询指定类型和日期的分析报告
    """
    try:
        # 统一日期格式处理
        report_date = datetime.strptime(date, "%Y-%m-%d")
        
        query = db.query(AnalysisReport).filter(
            AnalysisReport.report_date == report_date,
            AnalysisReport.report_type == report_type
        )
        if symbol:
            query = query.filter(AnalysisReport.symbol == symbol)
        
        report = query.first()
        
        if not report:
            return AnalysisResponse(
                success=False,
                message=f"未找到 {date} 的 {report_type} 分析报告",
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
