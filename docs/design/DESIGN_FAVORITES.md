# 自选股模块设计方案

## 背景

用户提出策略模块需要优化，核心需求是：
1. 用户可以订阅策略
2. 策略根据股票池给出买卖信号
3. 通知用户

本次规划重点：**设计自选模块**，用户在订阅策略时可以：
- 选择已有自选分组的股票
- 搜索股票并添加到自选/股票池

## 现有代码分析

| 组件 | 现状 | 路径 |
|------|------|------|
| 用户模型 | 已有 | `backend/app/models/user.py` |
| 股票模型 | 已有 | `backend/app/models/stock.py` |
| 股票搜索 | 已有 | `backend/app/services/market_data.py:search_stock()` |
| 策略模型 | 已有 | `backend/app/models/strategy.py` |
| 策略服务 | 已有 | `backend/app/services/strategy.py` |
| 持仓模型 | 已有 | `backend/app/models/portfolio.py` |

## 方案设计

### 1. 数据模型设计

#### 1.1 自选分组表 (StockGroup)
```python
class StockGroup(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)  # 分组名称，如"科技股"、"龙头股"
    description = Column(String(200))  # 描述
    is_default = Column(Boolean, default=False)  # 是否为默认分组
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

#### 1.2 自选股票表 (StockFavorite)
```python
class StockFavorite(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("stock_groups.id"), nullable=False)
    symbol = Column(String(10), nullable=False)
    name = Column(String(50), nullable=False)
    added_at = Column(DateTime, server_default=func.now())
```

#### 1.3 策略订阅表 (StrategySubscription)
```python
class StrategySubscription(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    stock_pool_type = Column(String(20))  # "all" | "group" | "custom"
    stock_group_id = Column(Integer, ForeignKey("stock_groups.id"), nullable=True)
    custom_symbols = Column(JSON, nullable=True)  # 自定义股票列表
    notify_enabled = Column(Boolean, default=True)
    notify_channels = Column(JSON, default=["websocket"])  # ["feishu", "websocket"]
    created_at = Column(DateTime, server_default=func.now())
```

### 2. API 端点设计

#### 自选分组管理
| 端点 | 方法 | 功能 |
|------|------|------|
| `/favorites/groups` | GET | 获取用户自选分组列表 |
| `/favorites/groups` | POST | 创建自选分组 |
| `/favorites/groups/{id}` | PUT | 更新分组 |
| `/favorites/groups/{id}` | DELETE | 删除分组 |

#### 自选股票管理
| 端点 | 方法 | 功能 |
|------|------|------|
| `/favorites/stocks` | GET | 获取自选股票列表（支持分组筛选） |
| `/favorites/stocks` | POST | 添加自选股票 |
| `/favorites/stocks/{id}` | DELETE | 删除自选股票 |
| `/favorites/stocks/search` | GET | 搜索股票（从数据库） |

#### 策略订阅
| 端点 | 方法 | 功能 |
|------|------|------|
| `/subscriptions` | GET | 获取订阅列表 |
| `/subscriptions` | POST | 订阅策略（可选择股票池） |
| `/subscriptions/{id}` | PUT | 更新订阅设置 |
| `/subscriptions/{id}` | DELETE | 取消订阅 |

### 3. 信号生成任务

```python
# backend/app/tasks/strategy_signal_tasks.py
@celery_app.task
def generate_signals_for_subscriptions():
    """为所有订阅用户生成信号"""
    # 1. 查询所有活跃订阅
    # 2. 根据订阅的股票池获取股票列表
    # 3. 调用策略服务生成信号
    # 4. 保存信号并触发通知
```

### 4. 前端页面设计

#### 4.1 自选管理页面 (`/favorites`)
- 左侧：分组列表（可添加/编辑/删除分组）
- 右侧：当前分组的股票列表
- 支持搜索添加股票
- 支持批量操作

#### 4.2 策略订阅页面 (`/subscriptions`)
- 策略选择器
- 股票池选择：
  - 全部自选股
  - 选择特定分组
  - 自定义股票列表
- 通知设置开关
- **通知渠道**：WebSocket 推送优先

### 5. 关键文件清单

| 文件 | 操作 |
|------|------|
| `backend/app/models/stock_group.py` | 新建 |
| `backend/app/models/stock_favorite.py` | 新建 |
| `backend/app/models/strategy_subscription.py` | 新建 |
| `backend/app/services/stock_favorite_service.py` | 新建 |
| `backend/app/services/subscription_service.py` | 新建 |
| `backend/app/api/endpoints/favorites.py` | 新建 |
| `backend/app/api/endpoints/subscriptions.py` | 新建 |
| `backend/app/tasks/strategy_signal_tasks.py` | 新建 |
| `frontend/web/src/pages/FavoritesPage.tsx` | 新建 |
| `frontend/web/src/pages/SubscriptionPage.tsx` | 新建 |
| `frontend/web/src/api/favorites.ts` | 新建 |
| `frontend/web/src/api/subscriptions.ts` | 新建 |

## 实现顺序

1. **第一阶段**：数据模型和服务
   - 创建 StockGroup、StockFavorite 模型
   - 实现自选分组和股票的 CRUD 服务

2. **第二阶段**：API 接口
   - 实现自选相关 API
   - 实现策略订阅 API

3. **第三阶段**：前端页面
   - 自选管理页面
   - 策略订阅页面

4. **第四阶段**：信号生成和通知
   - 实现定时任务生成信号
   - 集成通知服务

## 验证方式

1. 启动后端服务，测试 API 接口
2. 创建自选分组，添加股票
3. 订阅策略，选择股票池
4. 手动触发信号生成，验证通知
