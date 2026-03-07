# 雪球 Token 管理补充说明

## Token 获取机制

### 1. 自动获取流程

```python
# 首次调用时自动获取
if not self._is_xueqiu_token_valid():
    self._refresh_xueqiu_token()
```

**具体步骤**:
1. 清除旧 Cookie（避免干扰）
2. 访问 `https://xueqiu.com`（带完整浏览器请求头）
3. 从响应 Cookie 中提取 `xq_a_token`
4. 保存 Token 和获取时间戳
5. 后续请求复用 Session 中的 Cookie

### 2. Token 有效期管理

| 策略 | 说明 |
|------|------|
| **自动过期** | Token 使用超过 30 分钟后，下次调用时自动刷新 |
| **定时刷新** | Celery 每 30 分钟强制刷新，确保不过期 |
| **失效检测** | 接口返回 401/403 时，立即刷新并重试 |

### 3. 错误处理

**Token 失效场景**:
```
调用雪球接口
    ↓
返回 401/403
    ↓
检测错误码 → 触发 token 刷新
    ↓
重试原请求（最多1次）
    ↓
仍然失败 → 降级到东财
```

**Token 获取失败**:
- 连续 3 次尝试失败 → 放弃雪球，直接使用东财
- 记录错误日志，便于排查

### 4. 请求头配置

获取 Token 时使用完整浏览器请求头模拟:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,...',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}
```

### 5. Celery 定时任务

```python
# 每 30 分钟强制刷新
'refresh-xueqiu-token': {
    'task': 'app.tasks.price_tasks.refresh_xueqiu_token_task',
    'schedule': 1800.0,
}
```

**任务行为**:
- 正常情况：Token 更新，无感知
- 刷新失败：记录错误，下次调用时自动重试

### 6. 监控指标

可通过日志监控 Token 状态:
```bash
# 查看 Token 刷新日志
grep "雪球Token" logs/celery.log

# 查看 Token 失效
grep "Token.*失效" logs/app.log
```

### 7. 手动刷新

如需手动刷新 Token，可调用:
```python
from app.utils.stock_tool import stock_tool

# 强制刷新
stock_tool._ensure_xueqiu_token(force_refresh=True)
```
