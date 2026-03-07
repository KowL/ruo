"""
熔断器模块 - Circuit Breaker
实现失败率检测和自动降级机制
"""
import time
import logging
from enum import Enum
from typing import Callable, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常，请求通过
    OPEN = "open"          # 熔断，直接返回降级结果
    HALF_OPEN = "half_open"  # 半开，尝试恢复


class CircuitBreaker:
    """
    熔断器实现
    
    状态流转:
    CLOSED --(失败>=threshold)--> OPEN --(timeout)--> HALF_OPEN --(成功>=threshold)--> CLOSED
                                           └─(任一失败)--> OPEN
    
    使用示例:
        breaker = CircuitBreaker(name="eastmoney", failure_threshold=5)
        
        @breaker.protect(fallback=fallback_func)
        def fetch_data():
            return requests.get(url)
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 3,
        expected_exception: type = Exception
    ):
        """
        初始化熔断器
        
        Args:
            name: 熔断器名称，用于日志标识
            failure_threshold: 触发熔断的连续失败次数
            recovery_timeout: 熔断后尝试恢复的时间（秒）
            success_threshold: 半开状态下恢复所需的连续成功次数
            expected_exception: 需要捕获的异常类型
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        
    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        return self._state
    
    @property
    def is_open(self) -> bool:
        """是否处于熔断状态"""
        return self._state == CircuitState.OPEN
    
    def can_execute(self) -> bool:
        """
        检查是否可以执行请求
        
        Returns:
            True: 可以执行（CLOSED 或 HALF_OPEN 且超时）
            False: 熔断中，直接返回降级结果
        """
        if self._state == CircuitState.CLOSED:
            return True
        
        if self._state == CircuitState.OPEN:
            # 检查是否超过恢复时间
            if self._last_failure_time and \
               (time.time() - self._last_failure_time) >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                logger.info(f"[{self.name}] 熔断器进入半开状态，尝试恢复")
                return True
            return False
        
        # HALF_OPEN 状态允许执行
        return True
    
    def record_success(self):
        """记录成功"""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info(f"[{self.name}] 熔断器恢复关闭状态")
        else:
            # CLOSED 状态下重置失败计数
            self._failure_count = 0
    
    def record_failure(self):
        """记录失败"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            # 半开状态下任一失败都重新熔断
            self._state = CircuitState.OPEN
            logger.warning(f"[{self.name}] 半开状态失败，重新熔断")
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                f"[{self.name}] 熔断器触发，连续失败 {self._failure_count} 次"
            )
    
    def protect(self, fallback: Optional[Callable] = None):
        """
        装饰器：保护函数执行
        
        Args:
            fallback: 降级函数，当熔断时调用
        
        使用示例:
            @breaker.protect(fallback=lambda: cached_data)
            def fetch_from_api():
                return requests.get(url)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # 检查是否可以执行
                if not self.can_execute():
                    logger.debug(f"[{self.name}] 熔断器开启，执行降级逻辑")
                    if fallback:
                        return fallback(*args, **kwargs)
                    raise CircuitBreakerOpen(f"[{self.name}] 服务暂时不可用")
                
                try:
                    result = func(*args, **kwargs)
                    self.record_success()
                    return result
                except self.expected_exception as e:
                    self.record_failure()
                    if fallback:
                        logger.debug(f"[{self.name}] 执行失败，调用降级: {e}")
                        return fallback(*args, **kwargs)
                    raise
            
            return wrapper
        return decorator
    
    def get_stats(self) -> dict:
        """获取熔断器统计信息"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "success_threshold": self.success_threshold
            }
        }
    
    def reset(self):
        """手动重置熔断器"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        logger.info(f"[{self.name}] 熔断器手动重置")


class CircuitBreakerOpen(Exception):
    """熔断器开启异常"""
    pass


class DataSourceManager:
    """
    数据源管理器
    管理多个数据源的熔断状态
    """
    
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._fallback_order: list[str] = []
    
    def register(
        self,
        name: str,
        fetch_func: Callable,
        fallback_order: int = 0,
        **breaker_kwargs
    ):
        """
        注册数据源
        
        Args:
            name: 数据源名称
            fetch_func: 数据获取函数
            fallback_order: 降级优先级，数字越小优先级越高
            **breaker_kwargs: 熔断器配置
        """
        self._breakers[name] = {
            "breaker": CircuitBreaker(name, **breaker_kwargs),
            "fetch_func": fetch_func
        }
        
        # 按优先级排序
        self._fallback_order = sorted(
            self._breakers.keys(),
            key=lambda x: self._breakers[x].get("fallback_order", 0)
        )
    
    def fetch(self, *args, **kwargs) -> Any:
        """
        按优先级获取数据
        
        按 fallback_order 顺序尝试，直到成功或全部失败
        """
        last_error = None
        
        for name in self._fallback_order:
            breaker_info = self._breakers[name]
            breaker = breaker_info["breaker"]
            fetch_func = breaker_info["fetch_func"]
            
            if not breaker.can_execute():
                continue
            
            try:
                result = fetch_func(*args, **kwargs)
                breaker.record_success()
                return {"data": result, "source": name, "degraded": False}
            except Exception as e:
                breaker.record_failure()
                last_error = e
                logger.warning(f"[{name}] 获取数据失败: {e}")
        
        # 所有数据源都失败
        raise last_error or Exception("所有数据源均不可用")
    
    def get_health_status(self) -> dict:
        """获取所有数据源健康状态"""
        return {
            name: info["breaker"].get_stats()
            for name, info in self._breakers.items()
        }


# 全局熔断器实例
eastmoney_breaker = CircuitBreaker(
    name="eastmoney",
    failure_threshold=5,
    recovery_timeout=60.0,
    success_threshold=3
)

xueqiu_breaker = CircuitBreaker(
    name="xueqiu",
    failure_threshold=5,
    recovery_timeout=60.0,
    success_threshold=3
)
