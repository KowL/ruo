"""
价格更新任务 - Price Tasks
负责定时批量更新持仓股票的实时价格
"""
import logging
from typing import Dict
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

@shared_task(name='app.tasks.price_tasks.update_portfolio_prices_task')
def update_portfolio_prices_task() -> Dict:
    """
    批量更新持仓价格任务
    
    每 10-30 秒执行一次
    1. 获取所有激活持仓的股票代码
    2. 批量拉取实时行情
    3. 更新数据库中的 current_price
    """
    try:
        from app.core.database import get_db
        from app.services.market_data import get_market_data_service
        from app.models.portfolio import Portfolio

        # 0. 检查交易时间 (周一到周五, 09:00 - 15:00)
        # 注意：这里使用服务器本地时间（假设服务器在东八区）或者 UTC 转东八区
        # 简单起见，假设容器时区已设置为 Asia/Shanghai
        now = datetime.now()
        
        # 检查是否是周末 (5=Sat, 6=Sun)
        if now.weekday() >= 5:
            return {"status": "skipped", "reason": "not_trading_day_weekend"}
            
        # 检查时间段 (9:00 - 15:00)
        # 实际交易时间是 9:30-11:30, 13:00-15:00，但用户要求 9-15
        current_hour = now.hour
        if current_hour < 9 or current_hour >= 15:
            # 可以在 15:05 之前多跑几次以确保收盘价更新
            if not (current_hour == 15 and now.minute <= 5): 
                return {"status": "skipped", "reason": "not_trading_hour"}

        logger.info("[价格更新] 开始批量更新持仓价格")
        
        db: Session = next(get_db())
        market_service = get_market_data_service()

        # 1. 获取所有激活的持仓
        portfolios = db.query(Portfolio).filter(Portfolio.is_active == 1).all()
        
        if not portfolios:
            db.close()
            return {"status": "no_portfolios", "updated": 0}

        # 2. 提取不重复的股票代码
        symbols = list(set([p.symbol for p in portfolios]))
        # logger.info(f"[价格更新] 需更新 {len(symbols)} 只股票")

        # 3. 批量获取实时行情
        realtime_data = market_service.batch_get_realtime_prices(symbols)
        
        updated_count = 0
        
        # 4. 更新数据库
        for portfolio in portfolios:
            if portfolio.symbol in realtime_data:
                price_info = realtime_data[portfolio.symbol]
                new_price = price_info.get('price', 0.0)
                
                # 只有价格有效且变化超过一定阈值才更新（减少DB写入）
                # 这里为了实时性，只要变了就更
                if new_price > 0 and abs(portfolio.current_price - new_price) > 0.001:
                    portfolio.current_price = new_price
                    updated_count += 1
        
        if updated_count > 0:
            db.commit()
            logger.info(f"[价格更新] 成功更新 {updated_count} 条持仓价格")
        
        db.close()

        return {
            "status": "success",
            "updated_portfolios": updated_count,
            "total_symbols": len(symbols),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"[价格更新] 任务失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
