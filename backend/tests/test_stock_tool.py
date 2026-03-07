"""
StockTool 模块单元测试
测试文件: backend/tests/test_stock_tool.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from app.utils.stock_tool import StockTool, stock_tool


class TestStockToolBasic:
    """StockTool 基础功能测试"""
    
    def test_to_eastmoney_code_shanghai(self):
        """测试上海股票代码转换"""
        assert stock_tool._to_eastmoney_code("600000") == "1.600000"
        assert stock_tool._to_eastmoney_code("688001") == "1.688001"
    
    def test_to_eastmoney_code_shenzhen(self):
        """测试深圳股票代码转换"""
        assert stock_tool._to_eastmoney_code("000001") == "0.000001"
        assert stock_tool._to_eastmoney_code("300001") == "0.300001"
        assert stock_tool._to_eastmoney_code("002001") == "0.002001"
    
    def test_from_eastmoney_code(self):
        """测试东财代码转回标准代码"""
        assert stock_tool._from_eastmoney_code("1.600000") == "600000"
        assert stock_tool._from_eastmoney_code("0.000001") == "000001"
        assert stock_tool._from_eastmoney_code("600000") == "600000"
    
    def test_to_xueqiu_code(self):
        """测试雪球代码转换"""
        assert stock_tool._to_xueqiu_code("600000") == "SH600000"
        assert stock_tool._to_xueqiu_code("000001") == "SZ000001"
        assert stock_tool._to_xueqiu_code("300001") == "SZ300001"
        assert stock_tool._to_xueqiu_code("800001") == "BJ800001"


class TestEastMoneyBatchFetch:
    """东财批量接口测试"""
    
    @patch.object(stock_tool, '_session')
    def test_fetch_eastmoney_batch_success(self, mock_session):
        """测试东财批量接口成功返回"""
        # 模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "diff": [
                    {
                        "f12": "000001",  # 代码
                        "f13": 0,         # 市场
                        "f14": "平安银行", # 名称
                        "f2": 10.50,      # 最新价
                        "f3": 2.35,       # 涨跌幅
                        "f4": 0.24,       # 涨跌额
                        "f5": 123456,     # 成交量(手)
                        "f6": 123456789,  # 成交额
                        "f15": 10.60,     # 最高
                        "f16": 10.20,     # 最低
                        "f17": 10.30,     # 开盘
                        "f18": 10.26,     # 昨收
                        "f20": 2000000000,  # 总市值
                        "f21": 1500000000,  # 流通市值
                    }
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        
        result = stock_tool._fetch_eastmoney_batch(["000001"])
        
        assert "000001" in result
        assert result["000001"]["name"] == "平安银行"
        assert result["000001"]["price"] == 10.50
        assert result["000001"]["changePct"] == 2.35
        assert result["000001"]["volume"] == 12345600  # 转换为股
        assert result["000001"]["source"] == "eastmoney"
    
    @patch.object(stock_tool, '_session')
    def test_fetch_eastmoney_batch_empty_response(self, mock_session):
        """测试空响应处理"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        
        result = stock_tool._fetch_eastmoney_batch(["000001"])
        
        assert result == {}
    
    @patch.object(stock_tool, '_session')
    def test_fetch_eastmoney_batch_request_error(self, mock_session):
        """测试请求异常处理"""
        mock_session.get.side_effect = Exception("Network error")
        
        result = stock_tool._fetch_eastmoney_batch(["000001"])
        
        assert result == {}
    
    @patch.object(stock_tool, '_fetch_eastmoney_batch')
    def test_get_batch_realtime_eastmoney_batched(self, mock_fetch):
        """测试分批处理超过100只股票"""
        # 模拟返回数据
        def side_effect(symbols):
            return {s: {"price": 10.0} for s in symbols}
        
        mock_fetch.side_effect = side_effect
        
        # 生成150只股票
        symbols = [f"{i:06d}" for i in range(150)]
        result = stock_tool.get_batch_realtime_eastmoney(symbols)
        
        # 应调用 2 次（100 + 50）
        assert mock_fetch.call_count == 2
        assert len(result) == 150


class TestXueqiuTokenManagement:
    """雪球 Token 管理测试"""
    
    @patch.object(stock_tool, '_session')
    def test_refresh_xueqiu_token_success(self, mock_session):
        """测试 Token 刷新成功"""
        # 设置 mock cookies 的返回值
        mock_cookies = MagicMock()
        mock_cookies.get_dict.return_value = {'xq_a_token': 'test_token123'}
        mock_session.cookies = mock_cookies
        
        mock_response = Mock()
        mock_response.headers = {'set-cookie': 'xq_a_token=test_token123;'}
        mock_session.get.return_value = mock_response
        
        result = stock_tool._refresh_xueqiu_token()
        
        assert result is True
        assert stock_tool._xueqiu_token == "test_token123"
    
    @patch.object(stock_tool, '_session')
    def test_refresh_xueqiu_token_failure(self, mock_session):
        """测试 Token 刷新失败"""
        mock_session.get.side_effect = Exception("Connection error")
        
        result = stock_tool._refresh_xueqiu_token()
        
        assert result is False
    
    def test_is_xueqiu_token_valid_no_token(self):
        """测试无 Token 时返回无效"""
        stock_tool._xueqiu_token = None
        
        result = stock_tool._is_xueqiu_token_valid()
        
        assert result is False
    
    def test_is_xueqiu_token_valid_expired(self):
        """测试过期 Token"""
        stock_tool._xueqiu_token = "old_token"
        stock_tool._xueqiu_token_time = 0  # 很久以前
        
        result = stock_tool._is_xueqiu_token_valid()
        
        assert result is False
    
    def test_is_xueqiu_token_valid_fresh(self):
        """测试有效 Token"""
        import time
        stock_tool._xueqiu_token = "fresh_token"
        stock_tool._xueqiu_token_time = time.time()
        
        result = stock_tool._is_xueqiu_token_valid()
        
        assert result is True


class TestXueqiuBatchFetch:
    """雪球批量接口测试"""
    
    @patch.object(stock_tool, '_ensure_xueqiu_token')
    @patch.object(stock_tool, '_session')
    def test_fetch_xueqiu_batch_success(self, mock_session, mock_ensure_token):
        """测试雪球批量接口成功"""
        mock_ensure_token.return_value = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "items": [
                    {
                        "quote": {
                            "symbol": "SH600000",
                            "name": "浦发银行",
                            "current": 10.5,
                            "percent": 2.5,
                            "change": 0.25,
                            "volume": 1000000,
                            "amount": 10500000,
                            "high": 10.8,
                            "low": 10.2,
                            "open": 10.3,
                            "last_close": 10.25,
                            "market_capital": 2000000000,
                            "float_market_capital": 1500000000,
                            "pe_ttm": 5.5,
                            "pb": 0.8
                        }
                    }
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        
        result = stock_tool._fetch_xueqiu_batch(["600000"])
        
        assert "600000" in result
        assert result["600000"]["name"] == "浦发银行"
        assert result["600000"]["source"] == "xueqiu"
    
    @patch.object(stock_tool, '_ensure_xueqiu_token')
    def test_fetch_xueqiu_batch_no_token(self, mock_ensure_token):
        """测试无 Token 时返回空"""
        mock_ensure_token.return_value = False
        
        result = stock_tool.get_batch_realtime_xueqiu(["600000"])
        
        assert result == {}
    
    @patch.object(stock_tool, '_ensure_xueqiu_token')
    @patch.object(stock_tool, '_session')
    def test_fetch_xueqiu_batch_auth_error_retry(self, mock_session, mock_ensure_token):
        """测试 401 错误触发重试"""
        # 第一次返回 401，第二次成功
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"data": {"items": []}}
        mock_response_success.raise_for_status = Mock()
        
        mock_session.get.side_effect = [mock_response_401, mock_response_success]
        mock_ensure_token.return_value = True
        
        result = stock_tool._fetch_xueqiu_batch(["600000"])
        
        # 应调用 ensure_token 进行刷新
        mock_ensure_token.assert_called_with(force_refresh=True)


class TestUnifiedRealtimeQuotes:
    """统一实时行情接口测试"""
    
    @patch.object(stock_tool, 'get_batch_realtime_eastmoney')
    def test_unified_prefer_eastmoney_success(self, mock_eastmoney):
        """测试优先东财成功"""
        mock_eastmoney.return_value = {
            "000001": {"price": 10.5, "name": "平安银行"}
        }
        
        result = stock_tool.get_realtime_quotes_unified(
            ["000001"], 
            prefer_source='eastmoney'
        )
        
        assert "000001" in result
        assert result["000001"]["degraded"] is False
    
    @patch.object(stock_tool, 'get_batch_realtime_eastmoney')
    @patch.object(stock_tool, 'get_batch_realtime_xueqiu')
    def test_unified_eastmoney_fail_fallback_xueqiu(
        self, mock_xueqiu, mock_eastmoney
    ):
        """测试东财失败降级到雪球"""
        mock_eastmoney.return_value = {}  # 失败
        mock_xueqiu.return_value = {
            "000001": {"price": 10.5, "name": "平安银行"}
        }
        
        result = stock_tool.get_realtime_quotes_unified(
            ["000001"],
            prefer_source='eastmoney'
        )
        
        assert "000001" in result
        assert result["000001"]["degraded"] is True
    
    @patch.object(stock_tool, 'get_batch_realtime_eastmoney')
    @patch.object(stock_tool, 'get_batch_realtime_xueqiu')
    def test_unified_partial_fallback(
        self, mock_xueqiu, mock_eastmoney
    ):
        """测试部分缺失时雪球补全"""
        # 东财只返回一只股票
        mock_eastmoney.return_value = {
            "000001": {"price": 10.5, "name": "平安银行"}
        }
        # 雪球补全另一只
        mock_xueqiu.return_value = {
            "600000": {"price": 20.0, "name": "浦发银行"}
        }
        
        result = stock_tool.get_realtime_quotes_unified(
            ["000001", "600000"],
            prefer_source='eastmoney'
        )
        
        assert len(result) == 2
        assert result["000001"]["degraded"] is False
        assert result["600000"]["degraded"] is True


class TestStockToolIntegration:
    """集成测试"""
    
    def test_code_conversion_roundtrip(self):
        """测试代码转换往返"""
        original_codes = ["000001", "600000", "300001", "688001"]
        
        for code in original_codes:
            # 东财格式
            em_code = stock_tool._to_eastmoney_code(code)
            recovered = stock_tool._from_eastmoney_code(em_code)
            assert recovered == code, f"东财格式转换失败: {code}"
    
    @patch.object(stock_tool, '_fetch_eastmoney_batch')
    @patch.object(stock_tool, '_fetch_xueqiu_batch')
    def test_full_workflow_with_fallback(
        self, mock_xueqiu_fetch, mock_eastmoney_fetch
    ):
        """
        完整工作流程测试:
        1. 尝试东财获取
        2. 部分股票缺失，雪球补全
        3. 验证降级标记
        """
        # 东财返回部分数据
        mock_eastmoney_fetch.return_value = {
            "000001": {
                "symbol": "000001",
                "name": "平安银行",
                "price": 10.5,
                "source": "eastmoney"
            }
        }
        
        # 雪球返回补全数据
        mock_xueqiu_fetch.return_value = {
            "600000": {
                "symbol": "600000",
                "name": "浦发银行",
                "price": 20.0,
                "source": "xueqiu"
            }
        }
        
        # 注意：这里需要 patch get_batch_realtime_eastmoney 和 get_batch_realtime_xueqiu
        with patch.object(stock_tool, 'get_batch_realtime_eastmoney') as mock_em, \
             patch.object(stock_tool, 'get_batch_realtime_xueqiu') as mock_xq:
            
            mock_em.return_value = {
                "000001": {"symbol": "000001", "name": "平安银行", "price": 10.5}
            }
            mock_xq.return_value = {
                "600000": {"symbol": "600000", "name": "浦发银行", "price": 20.0}
            }
            
            result = stock_tool.get_realtime_quotes_unified(
                ["000001", "600000"],
                prefer_source='eastmoney'
            )
            
            assert len(result) == 2
            assert result["000001"]["degraded"] is False
            assert result["600000"]["degraded"] is True
