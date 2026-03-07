"""
新闻服务测试
测试 akshare 新闻接口
"""
import pytest


def test_stock_zh_a_hist():
    """测试股票历史数据接口"""
    import akshare as ak
    
    stock_zh_a_hist_df = ak.stock_zh_a_hist(
        symbol="600734",
        period="daily",
        start_date="20050501",
        end_date="20050520",
        adjust="hfq"
    )
    
    assert stock_zh_a_hist_df is not None
    assert len(stock_zh_a_hist_df) > 0


def test_stock_news_em():
    """测试股票新闻接口"""
    import akshare as ak
    
    stock_news_em_df = ak.stock_news_em(symbol="603777")
    
    assert stock_news_em_df is not None
