# API 测试报告

**测试时间**: 2026-03-06 22:52  
**测试环境**: 本地开发环境 (macOS)  
**服务端口**: 8001

---

## 测试概览

| 接口 | 状态 | 响应时间 | 说明 |
|------|------|----------|------|
| 数据源健康检查 | ✅ 通过 | ~50ms | 返回东财/雪球熔断器状态 |
| 单股实时行情 | ✅ 通过 | ~200ms | 返回完整股票数据 |
| 批量实时行情(2只) | ✅ 通过 | ~90ms | 返回多股数据 |
| 批量实时行情(50只) | ✅ 通过 | ~340ms | 返回48只，无降级 |

---

## 详细测试结果

### 1. 数据源健康检查 API

**请求**:
```bash
GET /api/v1/market/health
```

**响应**:
```json
{
    "code": 200,
    "data": {
        "eastmoney": {
            "name": "eastmoney",
            "state": "closed",
            "failure_count": 0,
            "success_count": 0,
            "config": {
                "failure_threshold": 5,
                "recovery_timeout": 60.0,
                "success_threshold": 3
            }
        },
        "xueqiu": {
            "name": "xueqiu",
            "state": "closed",
            "success_threshold": 3
        }
    },
    "summary": {
        "all_healthy": true,
        "total_sources": 2,
        "healthy_sources": 2
    }
}
```

**验证点**:
- ✅ 返回 code 200
- ✅ 包含东财和雪球两个数据源
- ✅ state 均为 closed（正常状态）
- ✅ summary 显示 all_healthy: true

---

### 2. 单股实时行情 API

**请求**:
```bash
GET /api/v1/market/realtime/000001
```

**响应时间**: ~200ms

**响应**:
```json
{
    "code": 200,
    "data": {
        "symbol": "000001",
        "name": "平安银行",
        "price": 10.82,
        "change": 0.01,
        "changePct": 0.09,
        "open": 10.78,
        "high": 10.84,
        "low": 10.77,
        "close": 10.81,
        "volume": 47657700,
        "amount": 514733549.73,
        "marketCap": 209972034902,
        "floatMarketCap": 209968599065,
        "source": "eastmoney",
        "degraded": false,
        "timestamp": "2026-03-06 22:52:32"
    }
}
```

**验证点**:
- ✅ 返回 code 200
- ✅ symbol/name/price 等基础字段正确
- ✅ changePct 涨跌幅计算正确
- ✅ volume 成交量单位正确（股）
- ✅ source 标识为 eastmoney
- ✅ degraded 为 false（未降级）
- ✅ timestamp 时间戳正确

---

### 3. 批量实时行情 API

**请求**:
```bash
GET /api/v1/market/batch-realtime?symbols=000001,600000
```

**响应时间**: ~90ms

**响应**:
```json
{
    "code": 200,
    "data": {
        "000001": {
            "symbol": "000001",
            "name": "平安银行",
            "price": 10.82,
            "changePct": 0.09,
            "volume": 47657700,
            "source": "eastmoney",
            "degraded": false
        },
        "600000": {
            "symbol": "600000",
            "name": "浦发银行",
            "price": 9.89,
            "changePct": 1.12,
            "volume": 72726000,
            "source": "eastmoney",
            "degraded": false
        }
    },
    "meta": {
        "total": 2,
        "requested": 2,
        "degraded": 0
    }
}
```

**验证点**:
- ✅ 返回所有请求的股票
- ✅ meta 信息正确（total/requested/degraded）
- ✅ 响应时间 < 100ms（2只股票）

---

### 4. 大批量查询性能测试

**请求**:
```bash
GET /api/v1/market/batch-realtime?symbols=000001,600000,... (50只)
```

**响应时间**: ~340ms

**结果**:
- 请求股票数: 50只
- 返回股票数: 48只（2只无效代码）
- 降级数量: 0
- 数据源: 全部为 eastmoney

**验证点**:
- ✅ 批量查询性能良好（< 500ms）
- ✅ 自动过滤无效股票代码
- ✅ 50只股票未触发限流

---

## 测试结论

### 功能验证

| 功能 | 状态 |
|------|------|
| 数据源健康检查 | ✅ 正常 |
| 东财批量接口 | ✅ 正常 |
| 雪球 Token 管理 | ✅ 未触发（东财正常） |
| 熔断降级机制 | ✅ 未触发（东财正常） |
| 分级缓存 | ✅ 正常（第二次查询更快） |
| 字段完整性 | ✅ 所有必需字段已返回 |

### 性能指标

| 指标 | 目标值 | 实测值 | 状态 |
|------|--------|--------|------|
| 单股查询延迟 | < 500ms | ~200ms | ✅ |
| 批量查询(2只) | < 200ms | ~90ms | ✅ |
| 批量查询(50只) | < 500ms | ~340ms | ✅ |

### 风险提示

1. **雪球 Token 未测试**: 当前东财数据源正常，雪球作为备用的降级逻辑未实际触发
2. **熔断逻辑未测试**: 需要模拟东财接口失败场景来验证降级逻辑
3. **并发性能未测试**: 当前为单用户测试，多用户并发场景需要进一步验证

---

## 建议

1. **补充降级测试**: 手动配置错误东财 URL，验证雪球降级是否正常
2. **压力测试**: 使用工具如 wrk/ab 进行并发压力测试
3. **监控接入**: 将 health 接口接入 Prometheus 监控
