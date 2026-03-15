---
trigger: always_on
---

# Ruo 项目开发规约

## 一、基本规则

1. 用**中文（简体）**进行回复和注释。
2. 项目使用 **uv** 管理 Python 依赖，不使用 pip。
3. 测试脚本放在 `tests/` 目录下。
4. 不要重复添加实体和 API。
5. 前端样式要统一。
6. 新增功能前，先检查是否已有类似模块，避免重复建设。

## 二、后端目录规范

### 各层职责

| 目录 | 职责 | 禁止 |
|------|------|------|
| `core/` | 全局基础设施：config、database、llm_factory、websocket_manager | 不放业务逻辑、数据转换工具 |
| `services/` | 业务逻辑，每个服务类对应一个业务领域 | 不直接调用外部 API，通过 `utils/stock_tool.py` |
| `api/endpoints/` | 路由定义、参数校验、响应格式化 | 不写业务逻辑，调用 service 层 |
| `models/` | SQLAlchemy ORM 模型定义 | 不放查询逻辑 |
| `utils/` | 工具类：`stock_tool`（外部数据）、`data_converter`（类型转换）、`agent_browser`（浏览器） | 不放业务逻辑 |
| `tasks/` | Celery 异步任务定义 | 不写复杂逻辑，调用 service |
| `crawlers/` | 数据爬虫实现 | 使用 `utils/agent_browser.py` 进行浏览器操作 |
| `llm_agent/` | LLM Agent 角色、工作流、状态、工具 | 使用 `core/llm_factory.py` 获取 LLM 实例 |

### 新增文件检查清单

- [ ] 确认该功能不与现有模块重复
- [ ] 文件放在正确的目录下
- [ ] 添加模块级 docstring（中文说明）
- [ ] 在 `api/__init__.py` 中注册路由（如有新端点）
- [ ] 在 `models/__init__.py` 中导出模型（如有新模型）
- [ ] 在 `database.py` 的 `init_db()` 中导入模型

## 三、编码规范

### 服务层模式

```python
# ✅ 无 DB 依赖的服务：全局单例
_service = None
def get_xxx_service():
    global _service
    if _service is None:
        _service = XxxService()
    return _service

# ✅ 有 DB 依赖的服务：工厂函数，每次新建
def get_xxx_service(db: Session) -> XxxService:
    return XxxService(db)
```

**禁止**：
- ❌ 按 `session_id` 缓存实例（内存泄漏）
- ❌ 函数属性单例 (`func._instance`)
- ❌ 同一功能多套单例实现

### 外部数据获取

所有外部市场数据必须通过 `utils/stock_tool.py` 的 `StockTool` 类获取。

```python
# ✅ 正确
from app.utils.stock_tool import stock_tool
df = stock_tool.get_market_data_list(symbol=code, period="daily")

# ❌ 禁止直接调用
import akshare as ak
df = ak.stock_zh_a_hist(...)
```

### LLM 实例获取

```python
# ✅ 使用 LLMFactory
from app.core.llm_factory import LLMFactory, create_llm

llm = LLMFactory.get_instance()     # 共享单例
llm = create_llm(model="xxx")       # 新建实例
```

### 异常处理

```python
# ✅ 具体异常，有意义的日志
try:
    result = service.do_something()
except ValueError as e:
    logger.warning(f"参数错误: {e}")
    raise HTTPException(status_code=400, detail=str(e))

# ❌ 吞掉所有异常
try:
    result = service.do_something()
except Exception:
    pass  # 禁止！
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | snake_case | `market_data.py` |
| 类名 | PascalCase | `MarketDataService` |
| 函数 | snake_case | `get_market_data` |
| API 路由前缀 | kebab-case | `/concept-monitor` |
| Celery 任务名 | kebab-case | `sync-daily-prices` |
| 数据库表名 | snake_case | `daily_prices` |

## 四、API 路由规范

### 注册顺序

`api/__init__.py` 中按以下业务分组注册，新增路由放入对应分组：

```
核心业务:    portfolio, stock, news
策略回测:    strategy, backtest
行情市场:    dashboard, concepts, concept_monitor, dragon_tiger
分析智能:    sentiment, daily_report, alerts, analysis
```

### 接口设计

```python
# ✅ 统一响应格式
return {"status": "success", "data": result}
return {"status": "success", "data": result, "count": len(result)}

# ✅ 必须有 summary 和 tags
@router.get("/latest", summary="获取最新数据", tags=["模块名"])

# ✅ 参数使用 Query + 校验
days: int = Query(7, ge=1, le=30, description="天数")
```

## 五、模型层规范

- 每个模型文件对应一张或一组关联表
- 新模型**必须**在 `models/__init__.py` 中导出
- 新模型**必须**在 `database.py` 的 `init_db()` 中导入
- 三表结构（`DailyPrice`/`WeeklyPrice`/`MonthlyPrice`）是行情存储的标准模式

## 六、Celery 任务规范

- 任务名用 **kebab-case**，与功能一致（不能名实不符）
- 任务函数只做参数解析和 service 调用
- 必须设置 `autoretry_for`、`max_retries`、`retry_backoff`
- `beat_schedule` 中每个任务必须有注释

## 七、测试规范

- 测试文件放在 `tests/` 目录下
- 文件命名 `test_<模块名>.py`
- 使用 `pytest` 框架
- 运行命令：`cd backend && uv run python -m pytest tests/ -v`

---

## 八、前端目录规范

技术栈：**Vite + React 18 + TypeScript + TailwindCSS 3 + Zustand + ECharts**

### 各层职责

| 目录 | 职责 | 禁止 |
|------|------|------|
| `api/` | API 请求函数，每个文件对应一个后端模块 | 不定义 `interface`，类型放 `types/` |
| `pages/` | 页面级组件，对应路由 | 不定义可复用工具函数 |
| `components/` | 可复用 UI 组件，按功能分子目录 | 不直接调用 API，通过 props 或 store |
| `types/` | TypeScript 类型/接口定义 | 不放逻辑代码 |
| `hooks/` | 自定义 React Hooks | 不放 UI 代码 |
| `store/` | Zustand 状态管理 | 不放 UI 代码 |
| `utils/` | 纯工具函数（格式化、颜色、计算） | 不放业务逻辑 |
| `styles/` | CSS 变量（`theme.css`）+ Tailwind 层（`index.css`） | 不在组件内写内联 CSS 变量 |

### 新增文件检查清单

- [ ] 类型定义放在 `types/` 目录，不在 `api/` 中定义 `interface`
- [ ] 工具函数检查 `utils/format.ts` 是否已有类似实现
- [ ] 新页面在 `App.tsx` 中注册路由
- [ ] 新组件按功能放入 `components/` 对应子目录

## 九、前端编码规范

### 类型定义

```typescript
// ✅ 类型统一放 types/ 目录
// types/sentiment.ts
export interface SentimentIndex { ... }

// api/sentiment.ts — 只导入类型，不定义
import { SentimentIndex } from '@/types/sentiment';
export const getLatestSentiment = async (): Promise<SentimentIndex> => { ... };

// ❌ 禁止在 api/ 文件中定义 interface
```

### 工具函数

```typescript
// ✅ 通用函数放 utils/format.ts，页面导入复用
import { getProfitColor, getProfitBgColor, formatPercent } from '@/utils/format';

// ❌ 禁止在页面组件内重复定义工具函数
const getProfitColor = (percent: number) => { ... }; // 不要这样做
```

### 状态管理

```typescript
// ✅ 多页面共享数据使用 Zustand store
import { usePortfolioStore } from '@/store/portfolioStore';

// ✅ 页面内私有数据使用 useState
const [localData, setLocalData] = useState(null);

// ❌ 禁止在页面内硬编码 mock 数据用于生产
```

### API 调用

```typescript
// ✅ 使用 api/client.ts 统一的 axios 实例
import client from './client';

// ✅ AI 类长耗时请求单独设置超时
const response = await client.get('/analysis/run', { timeout: 120000 });

// ❌ 禁止直接使用 axios 或 fetch
```

### 环境变量

```typescript
// ✅ Vite 项目使用 import.meta.env
const wsHost = import.meta.env.VITE_WS_HOST;

// ❌ 禁止使用 CRA 格式
const wsHost = process.env.REACT_APP_WS_HOST; // Vite 中永远为 undefined
```

### 调试代码

- **禁止**提交 `console.log` 到生产代码（WebSocket 连接日志除外）
- 使用 `console.error` 仅在错误处理分支中

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `DashboardPage.tsx` |
| Hook 文件 | camelCase + `use` 前缀 | `useWebSocket.ts` |
| API 文件 | camelCase | `conceptMonitor.ts` |
| 类型文件 | camelCase | `strategy.ts` |
| CSS 变量 | kebab-case + `--color-` 前缀 | `--color-surface-1` |

## 十、前端 CSS 规范

- CSS 变量定义在 `styles/theme.css` 的 `:root` 中
- Tailwind 组件层定义在 `styles/index.css` 的 `@layer components`
- **不要**在 `theme.css` 和 `index.css` 中重复定义同名类
- 涨跌颜色使用 CSS 变量：`--color-profit-up`（红涨）、`--color-loss-up`（绿跌）
- 使用 Tailwind 的路径别名 `@` 指向 `src/`