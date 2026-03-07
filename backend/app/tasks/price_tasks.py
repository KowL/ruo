"""
价格更新任务 - Price Tasks v1.1
负责定时批量更新持仓股票的实时价格
优化：精细交易时段控制 + 数据源健康监控
"""
import logging
from typing import Dict, Tuple
from datetime import datetime, timezone, time
from celery import shared_task
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_trading_period(now: datetime) -> Tuple[bool, str]:
    """
    判断当前交易时段
    
    Returns:
        (是否交易时间, 时段类型)
        时段类型: pre_open(集合竞价), morning(早盘), afternoon(午盘), 
                close_auction(收盘竞价), closed(闭市)
    """
    weekday = now.weekday()
    current_time = now.time()
    
    # 周末
    if weekday >= 5:
        return False, "weekend"
    
    # 定义交易时段
    pre_open_start = time(9, 15)
    pre_open_end = time(9, 25)
    morning_start = time(9, 30)
    morning_end = time(11, 30)
    afternoon_start = time(13, 0)
    afternoon_end = time(14, 57)
    close_auction_end = time(15, 0)
    
    if pre_open_start <= current_time < pre_open_end:
        return True, "pre_open"  # 开盘集合竞价
    elif morning_start <= current_time <= morning_end:
        return True, "morning"   # 早盘
    elif afternoon_start <= current_time < afternoon_end:
        return True, "afternoon" # 午盘
    elif afternoon_end <= current_time <= close_auction_end:
        return True, "close_auction"  # 收盘集合竞价
    elif time(15, 0) < current_time <= time(15, 5):
        return True, "post_close"  # 盘后5分钟，确保收盘价更新
    else:
        return False, "closed"


@shared_task(name='app.tasks.price_tasks.update_portfolio_prices_task')
def update_portfolio_prices_task() -> Dict:
    """
    批量更新持仓价格任务
    
    每 10 秒执行一次（Celery Beat配置）
    1. 精细化判断交易时段
    2. 获取所有激活持仓的股票代码
    3. 批量拉取实时行情（东财主力 + 雪球备用）
    4. 更新数据库中的 current_price
    """
    try:
        from app.core.database import get_db
        from app.services.market_data import get_market_data_service
        from app.models.portfolio import Portfolio

        now = datetime.now()
        is_trading, period = get_trading_period(now)
        
        if not is_trading:
            return {
                "status": "skipped", 
                "reason": period,
                "time": now.strftime("%Y-%m-%d %H:%M:%S")
            }

        logger.info(f"[价格更新] 交易时段: {period}，开始批量更新持仓价格")
        
        db: Session = next(get_db())
        market_service = get_market_data_service()

        # 1. 获取所有激活的持仓
        portfolios = db.query(Portfolio).filter(Portfolio.is_active == 1).all()
        
        if not portfolios:
            db.close()
            return {"status": "no_portfolios", "updated": 0}

        # 2. 提取不重复的股票代码
        symbols = list(set([p.symbol for p in portfolios]))
        logger.info(f"[价格更新] 需更新 {len(symbols)} 只股票")

        # 3. 批量获取实时行情（自动处理东财/雪球切换）
        realtime_data = market_service.batch_get_realtime_prices(symbols)
        
        # 4. 检查数据源降级情况
        degraded_count = sum(1 for d in realtime_data.values() if d.get('degraded'))
        if degraded_count > 0:
            logger.warning(f"[价格更新] {degraded_count}/{len(realtime_data)} 只股票使用降级数据源")
        
        # 5. 更新数据库
        updated_count = 0
        failed_symbols = []
        
        for portfolio in portfolios:
            if portfolio.symbol in realtime_data:
                price_info = realtime_data[portfolio.symbol]
                new_price = price_info.get('price', 0.0)
                
                # 价格有效性检查
                if new_price <= 0:
                    failed_symbols.append(portfolio.symbol)
                    continue
                
                # 价格变化阈值控制（减少DB写入）
                price_changed = abs(portfolio.current_price - new_price) > 0.001
                
                if price_changed:
                    portfolio.current_price = new_price
                    portfolio.change_pct = price_info.get('changePct', 0)
                    updated_count += 1
            else:
                failed_symbols.append(portfolio.symbol)
        
        if updated_count > 0:
            db.commit()
        
        if failed_symbols:
            logger.warning(f"[价格更新] {len(failed_symbols)} 只股票未能获取价格")
        
        db.close()

        # 6. 获取数据源健康状态
        health_status = market_service.get_datasource_health()

        return {
            "status": "success",
            "updated_portfolios": updated_count,
            "total_symbols": len(symbols),
            "failed_symbols": len(failed_symbols),
            "degraded_count": degraded_count,
            "trading_period": period,
            "datasource_health": {
                name: stats['state'] 
                for name, stats in health_status.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"[价格更新] 任务失败: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@shared_task(name='app.tasks.price_tasks.check_datasource_health_task')
def check_datasource_health_task() -> Dict:
    """
    定期检查数据源健康状态
    每 5 分钟执行一次
    """
    try:
        from app.services.market_data import get_market_data_service
        
        market_service = get_market_data_service()
        health = market_service.get_datasource_health()
        
        # 检查是否有熔断的数据源
        open_breakers = [
            name for name, stats in health.items() 
            if stats['state'] == 'open'
        ]
        
        if open_breakers:
            logger.warning(f"[数据源健康] 以下数据源已熔断: {open_breakers}")
        
        return {
            "status": "success",
            "health": health,
            "open_breakers": open_breakers,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"[数据源健康] 检查失败: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name='app.tasks.price_tasks.refresh_xueqiu_token_task')
def refresh_xueqiu_token_task() -> Dict:
    """
    定时刷新雪球 Token
    每 30 分钟执行一次，确保 Token 有效性
    """
    try:
        from app.utils.stock_tool import stock_tool
        
        logger.info("[雪球Token] 开始刷新...")
        
        # 强制刷新 token
        success = stock_tool._ensure_xueqiu_token(force_refresh=True)
        
        if success:
            logger.info("[雪球Token] 刷新成功")
            return {
                "status": "success",
                "message": "Token refreshed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error("[雪球Token] 刷新失败")
            return {
                "status": "error",
                "message": "Token refresh failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        logger.error(f"[雪球Token] 刷新异常: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
