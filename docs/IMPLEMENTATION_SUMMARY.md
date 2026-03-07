# 实时行情数据方案 - 实现总结

> **更新日期**: 2026-03-06  
> **版本**: v1.1  
> **主数据源**: 东方财富 (EastMoney)  
> **备用数据源**: 雪球 (Xueqiu)

---

## 📁 文件变更清单

### 1. 新增文件

| 文件路径 | 说明 |
|----------|------|
| `docs/DESIGN_REALTIME_PRICE.md` | 详细设计文档 |
| `backend/app/core/circuit_breaker.py` | 熔断器模块 |

### 2. 修改文件

| 文件路径 | 变更说明 |
|----------|----------|
| `backend/app/utils/stock_tool.py` | 新增东财批量接口、雪球批量接口、统一接口 |
| `backend/app/services/market_data.py` | 集成熔断器、优化缓存策略、新增健康检查 |
| `backend/app/tasks/price_tasks.py` | 精细交易时段控制、数据源监控 |
| `backend/app/celery_config.py` | 启用价格任务、新增健康检查任务 |
| `backend/app/api/endpoints/market.py` | 新增批量查询、健康检查接口 |

---

## 🎯 核心功能实现

### 1. 东财批量实时行情接口

**接口**: `GET /api/v1/market/batch-realtime?symbols=000001,600000`

```json
{
  "code": 200,
  "data": {
    "000001": {
      "symbol": "000001",
      "name": "平安银行",
      "price": 10.50,
      "changePct": 2.35,
      "volume": 12345600,
      "source": "eastmoney",
      "degraded": false
    }
  },
  "meta": {
    "total": 1,
    "requested": 2,
    "degraded": 0
  }
}
```

### 2. 熔断降级机制

**触发条件**:
- 连续 5 次失败 → 熔断
- 熔断 60 秒后 → 半开状态
- 半开状态 3 次成功 → 恢复

**降级策略**:
```
东财批量接口 (主力)
    └── 失败/熔断 ──→ 雪球批量接口 (备用)
                           └── 失败 ──→ 返回缓存数据 + 降级标记
```

### 3. 分级缓存

| 数据类型 | TTL | 说明 |
|----------|-----|------|
| 实时价格 | 5秒 | 内存缓存 |
| 批量行情 | 5秒 | 内存缓存 |
| 盘口数据 | 3秒 | 内存缓存 |
| 分时数据 | 30秒 | 内存缓存 |
| 股票信息 | 1小时 | 内存缓存 |

### 4. 精细交易时段控制

```python
# 交易时段识别
pre_open      # 09:15-09:25 开盘集合竞价
morning       # 09:30-11:30 早盘
afternoon     # 13:00-14:57 午盘
close_auction # 14:57-15:00 收盘集合竞价
post_close    # 15:00-15:05 盘后更新
```

---

## 🚀 API 接口

### 新增接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/market/realtime/{symbol}` | 单股实时行情 |
| GET | `/api/v1/market/batch-realtime` | 批量实时行情 |
| GET | `/api/v1/market/health` | 数据源健康状态 |

### 响应字段

**实时行情数据**:
```json
{
  "symbol": "000001",
  "name": "平安银行",
  "price": 10.50,        // 最新价
  "change": 0.24,        // 涨跌额
  "changePct": 2.35,     // 涨跌幅%
  "open": 10.30,         // 开盘价
  "high": 10.60,         // 最高价
  "low": 10.20,          // 最低价
  "close": 10.26,        // 昨收价
  "volume": 12345600,    // 成交量(股)
  "amount": 123456789,   // 成交额(元)
  "marketCap": 2000000000,     // 总市值
  "floatMarketCap": 1500000000, // 流通市值
  "source": "eastmoney", // 数据来源
  "degraded": false,     // 是否降级
  "timestamp": "2026-03-06T14:30:00"
}
```

---

## ⚙️ Celery 定时任务

| 任务 | 频率 | 说明 |
|------|------|------|
| `update_portfolio_prices_task` | 每10秒 | 持仓价格更新（交易时段） |
| `check_datasource_health_task` | 每5分钟 | 数据源健康检查 |

---

## 📊 监控指标

### 熔断器状态

```python
{
  "eastmoney": {
    "state": "closed",        // closed/open/half_open
    "failure_count": 0,
    "success_count": 0,
    "config": {
      "failure_threshold": 5,
      "recovery_timeout": 60,
      "success_threshold": 3
    }
  },
  "xueqiu": { ... }
}
```

### 健康检查响应

```json
{
  "code": 200,
  "data": { ... },
  "summary": {
    "all_healthy": true,
    "total_sources": 2,
    "healthy_sources": 2
  }
}
```

---

## 🔧 环境变量配置

```bash
# 可选配置（使用默认值可不设置）
CACHE_L1_TTL=5                # 内存缓存5秒
CACHE_L2_TTL=30               # Redis缓存30秒
CIRCUIT_FAILURE_THRESHOLD=5   # 5次失败触发熔断
CIRCUIT_RECOVERY_TIMEOUT=60   # 60秒后尝试恢复
```

---

## 📈 性能目标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 批量接口 P99 延迟 | < 200ms | 100只股票批量查询 |
| 缓存命中率 | > 90% | L1 + L2 缓存 |
| 数据源切换时间 | < 1s | 主备切换耗时 |
| 降级感知时间 | < 30s | 从主源故障到降级 |

---

## ⚠️ 注意事项

1. **东财限流**: 批量接口建议单次不超过100只，批次间隔 > 100ms
2. **雪球Token**: 
   - 首次访问需要 1-2 秒获取 Token
   - Token 有效期约 2 小时，Celery 每 30 分钟自动刷新
   - Token 失效时会自动检测并重试
3. **熔断器状态**: 手动重置熔断器需要重启服务或调用重置接口
4. **缓存一致性**: 内存缓存非分布式，多实例部署需考虑一致性

### 雪球 Token 管理详情

**自动刷新机制**:
```
首次调用 → 自动获取 Token
    ↓
每 30 分钟 Celery 任务强制刷新
    ↓
接口返回 401/403 → 立即刷新并重试
```

**失败处理**:
- Token 获取失败 → 降级到东财接口
- 所有数据源失败 → 返回空数据 + 错误日志
- 连续失败会触发熔断器

---

## ✅ 测试覆盖

### 已创建测试文件

| 文件 | 测试数量 | 说明 |
|------|----------|------|
| `tests/test_circuit_breaker.py` | 17 | 熔断器状态机、降级、集成测试 |
| `tests/test_stock_tool.py` | 21 | 东财接口、雪球接口、Token 管理、集成测试 |

### 运行测试

```bash
cd /Volumes/mm/项目/ruo/backend

# 运行熔断器测试
uv run pytest tests/test_circuit_breaker.py -v

# 运行 stock_tool 测试
uv run pytest tests/test_stock_tool.py -v

# 运行全部测试
uv run pytest tests/ -v
```

### 测试结果

```
test_circuit_breaker.py: 17 passed
test_stock_tool.py: 21 passed
```
