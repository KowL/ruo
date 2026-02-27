"""
概念异动监控 API
Concept Monitor API
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.concept_monitor import get_concept_monitor_service

router = APIRouter()
service = get_concept_monitor_service()


@router.get("/movement-ranking", summary="概念涨幅排行", tags=["概念监控"])
async def get_movement_ranking(limit: Optional[int] = 20):
    """
    获取概念板块涨幅排行

    **参数:**
    - limit: 返回条数，默认20

    **返回:**
    - name: 板块名称
    - change_pct: 涨跌幅
    - total_mv: 总市值（亿元）
    - turnover: 换手率
    - up_count: 上涨家数
    - down_count: 下跌家数
    - limit_up_count: 涨停家数
    """
    try:
        data = service.get_concept_movement_ranking(limit)
        return {
            "status": "success",
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨幅排行失败: {str(e)}")


@router.get("/fund-flow", summary="资金流入排行", tags=["概念监控"])
async def get_fund_flow_ranking(limit: Optional[int] = 20):
    """
    获取概念板块资金流入排行

    **参数:**
    - limit: 返回条数，默认20

    **返回:**
    - name: 板块名称
    - main_net_inflow: 主力净流入（万元）
    - main_net_inflow_pct: 主力净流入占比
    - retail_net_inflow: 散户净流入（万元）
    - total_amount: 成交额（亿元）
    """
    try:
        data = service.get_fund_flow_ranking(limit)
        return {
            "status": "success",
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资金流入失败: {str(e)}")


@router.get("/limit-up-statistics", summary="涨停家数统计", tags=["概念监控"])
async def get_limit_up_statistics():
    """
    获取涨停家数统计，按概念分组

    **返回:**
    - total_limit_up: 总涨停家数
    - concept_ranking: 概念涨停排行
    - update_time: 更新时间
    """
    try:
        data = service.get_limit_up_statistics()
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨停统计失败: {str(e)}")


@router.get("/leading-stocks", summary="获取龙头股", tags=["概念监控"])
async def get_leading_stocks(concept_name: str, limit: Optional[int] = 5):
    """
    获取概念龙头股列表

    **参数:**
    - concept_name: 概念名称（板块名称）
    - limit: 返回条数，默认5

    **返回:**
    - symbol: 股票代码
    - name: 股票名称
    - price: 最新价
    - change_pct: 涨跌幅
    - turnover: 换手率
    - market_cap: 总市值（亿元）
    """
    try:
        data = service.get_leading_stocks(concept_name, limit)
        return {
            "status": "success",
            "data": data,
            "concept": concept_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取龙头股失败: {str(e)}")


@router.get("/market-overview", summary="市场概览", tags=["概念监控"])
async def get_market_overview():
    """
    获取市场概览数据

    **返回:**
    - up_count: 上涨家数
    - down_count: 下跌家数
    - flat_count: 平盘家数
    - limit_up_count: 涨停家数
    - limit_down_count: 跌停家数
    - total: 总家数
    - update_time: 更新时间
    """
    try:
        data = service.get_market_overview()
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")


@router.get("/dashboard", summary="概念监控仪表盘", tags=["概念监控"])
async def get_monitor_dashboard():
    """
    获取概念监控完整仪表盘数据

    **返回:**
    - movement_ranking: 涨幅排行
    - fund_flow_ranking: 资金流入排行
    - limit_up_statistics: 涨停统计
    - market_overview: 市场概览
    """
    try:
        data = {
            "movement_ranking": service.get_concept_movement_ranking(10),
            "fund_flow_ranking": service.get_fund_flow_ranking(10),
            "limit_up_statistics": service.get_limit_up_statistics(),
            "market_overview": service.get_market_overview(),
        }
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘失败: {str(e)}")
