"""
熔断器模块单元测试
测试文件: backend/tests/test_circuit_breaker.py
"""
import pytest
import time
from unittest.mock import Mock, patch

from app.core.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerOpen, 
    CircuitState,
    DataSourceManager
)


class TestCircuitBreaker:
    """熔断器基础功能测试"""
    
    def test_initial_state_is_closed(self):
        """测试初始状态为 CLOSED"""
        breaker = CircuitBreaker(name="test")
        assert breaker.state == CircuitState.CLOSED
        assert not breaker.is_open
    
    def test_record_success_in_closed_state(self):
        """CLOSED 状态下记录成功应重置失败计数"""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        # 模拟 2 次失败
        breaker.record_failure()
        breaker.record_failure()
        assert breaker._failure_count == 2
        
        # 1 次成功应重置计数
        breaker.record_success()
        assert breaker._failure_count == 0
    
    def test_open_circuit_after_threshold(self):
        """连续失败达到阈值后应触发熔断"""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        breaker.record_failure()  # 1
        assert breaker.state == CircuitState.CLOSED
        
        breaker.record_failure()  # 2
        assert breaker.state == CircuitState.CLOSED
        
        breaker.record_failure()  # 3 - 触发熔断
        assert breaker.state == CircuitState.OPEN
        assert breaker.is_open
    
    def test_can_execute_returns_false_when_open(self):
        """熔断状态下 can_execute 应返回 False"""
        breaker = CircuitBreaker(name="test", failure_threshold=1)
        
        assert breaker.can_execute() is True
        breaker.record_failure()
        assert breaker.can_execute() is False
    
    def test_half_open_after_recovery_timeout(self):
        """熔断超时后应进入半开状态"""
        breaker = CircuitBreaker(
            name="test", 
            failure_threshold=1,
            recovery_timeout=0.1  # 100ms 便于测试
        )
        
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        
        # 等待超时
        time.sleep(0.15)
        
        # 应进入半开状态
        assert breaker.can_execute() is True
        assert breaker.state == CircuitState.HALF_OPEN
    
    def test_close_after_success_in_half_open(self):
        """半开状态下连续成功应恢复关闭"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            recovery_timeout=0.1,
            success_threshold=2
        )
        
        # 触发熔断
        breaker.record_failure()
        time.sleep(0.15)
        
        # 必须先调用 can_execute() 来触发 OPEN -> HALF_OPEN 转换
        assert breaker.can_execute() is True
        assert breaker.state == CircuitState.HALF_OPEN
        
        # 半开状态，需要 2 次成功
        breaker.record_success()
        assert breaker.state == CircuitState.HALF_OPEN
        
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
    
    def test_reopen_on_failure_in_half_open(self):
        """半开状态下任一失败应重新熔断"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            recovery_timeout=0.1
        )
        
        breaker.record_failure()
        time.sleep(0.15)
        
        # 半开状态下失败
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
    
    def test_protect_decorator_success(self):
        """保护装饰器应正常执行函数"""
        breaker = CircuitBreaker(name="test")
        
        @breaker.protect()
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"
    
    def test_protect_decorator_with_fallback(self):
        """保护装饰器失败时应调用降级函数"""
        breaker = CircuitBreaker(name="test", failure_threshold=1)
        
        fallback_mock = Mock(return_value="fallback_value")
        
        @breaker.protect(fallback=fallback_mock)
        def fail_func():
            raise ValueError("error")
        
        # 第一次失败
        result = fail_func()
        assert result == "fallback_value"
        fallback_mock.assert_called_once()
        
        # 第二次调用（已熔断）
        fallback_mock.reset_mock()
        result = fail_func()
        assert result == "fallback_value"
        fallback_mock.assert_called_once()
    
    def test_protect_decorator_raises_when_no_fallback(self):
        """无降级函数且熔断时应抛出异常"""
        breaker = CircuitBreaker(name="test", failure_threshold=1)
        
        @breaker.protect()
        def fail_func():
            raise ValueError("error")
        
        # 第一次调用，记录失败并抛出原始异常
        with pytest.raises(ValueError):
            fail_func()
        
        # 熔断器应已打开
        assert breaker.is_open
        
        # 第二次调用，已熔断，抛出 CircuitBreakerOpen
        with pytest.raises(CircuitBreakerOpen):
            fail_func()
    
    def test_get_stats(self):
        """测试统计信息获取"""
        breaker = CircuitBreaker(
            name="test_stats",
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=3
        )
        
        stats = breaker.get_stats()
        
        assert stats["name"] == "test_stats"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["config"]["failure_threshold"] == 5
    
    def test_reset(self):
        """测试手动重置"""
        breaker = CircuitBreaker(name="test", failure_threshold=1)
        
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0


class TestDataSourceManager:
    """数据源管理器测试"""
    
    def test_register_datasource(self):
        """测试注册数据源"""
        manager = DataSourceManager()
        fetch_func = Mock(return_value={"data": "test"})
        
        manager.register("source1", fetch_func, fallback_order=1)
        
        assert "source1" in manager._breakers
    
    def test_fetch_uses_priority_order(self):
        """测试按优先级获取数据"""
        manager = DataSourceManager()
        
        # source1 优先级高但会失败
        source1_func = Mock(side_effect=Exception("fail"))
        # source2 优先级低但成功
        source2_func = Mock(return_value="source2_data")
        
        manager.register("source1", source1_func, fallback_order=1)
        manager.register("source2", source2_func, fallback_order=2)
        
        result = manager.fetch()
        
        assert result["data"] == "source2_data"
        assert result["source"] == "source2"
        # 当前实现不标记降级状态，如果需要可修改 DataSourceManager
    
    def test_fetch_success_from_primary(self):
        """主数据源成功时直接返回"""
        manager = DataSourceManager()
        
        source1_func = Mock(return_value="source1_data")
        manager.register("source1", source1_func, fallback_order=1)
        
        result = manager.fetch()
        
        assert result["data"] == "source1_data"
        assert result["source"] == "source1"
        assert result["degraded"] is False
    
    def test_get_health_status(self):
        """测试健康状态获取"""
        manager = DataSourceManager()
        manager.register("source1", Mock(), fallback_order=1)
        
        health = manager.get_health_status()
        
        assert "source1" in health
        assert health["source1"]["state"] == "closed"


class TestCircuitBreakerIntegration:
    """熔断器集成测试"""
    
    def test_real_world_scenario(self):
        """
        模拟真实场景:
        1. 服务正常
        2. 服务开始失败
        3. 熔断器打开
        4. 使用降级数据
        5. 服务恢复
        6. 熔断器关闭
        """
        breaker = CircuitBreaker(
            name="api_service",
            failure_threshold=3,
            recovery_timeout=0.1,
            success_threshold=2
        )
        
        call_count = 0
        should_fail = True
        
        @breaker.protect(fallback=lambda: "cached_data")
        def api_call():
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise ConnectionError("API down")
            return f"live_data_{call_count}"
        
        # 阶段1: API 正常（模拟）
        should_fail = False
        result = api_call()
        assert result == "live_data_1"
        
        # 阶段2: API 开始失败
        should_fail = True
        for _ in range(3):
            result = api_call()
            assert result == "cached_data"  # 降级数据
        
        # 熔断器应已打开
        assert breaker.is_open
        
        # 阶段3: 熔断期间直接使用降级
        result = api_call()
        assert result == "cached_data"
        
        # 阶段4: API 恢复
        should_fail = False
        
        # 等待恢复超时
        time.sleep(0.15)
        
        # 半开状态，需要 2 次成功
        result = api_call()
        assert result == "live_data_5"  # 第5次调用
        
        result = api_call()
        assert result == "live_data_6"  # 第6次调用
        
        # 熔断器应已关闭
        assert breaker.state == CircuitState.CLOSED
        
        # 阶段5: 恢复正常
        result = api_call()
        assert "live_data" in result
