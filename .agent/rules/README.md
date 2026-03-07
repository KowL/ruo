# 项目规则说明

本目录包含 Ruo 项目的开发规约和代码规范。

## 规则文件

| 文件 | 说明 |
|------|------|
| `project-rule.md` | 完整的项目开发规约（前后端规范、目录结构、编码标准等） |

## 对 AI 助手的要求

在协助开发本项目时，AI 助手**必须**遵守以下流程：

1. **开发前**
   - [ ] 阅读 `.agent/rules/project-rule.md` 文件
   - [ ] 理解项目的目录结构规范
   - [ ] 熟悉后端/前端的编码规范
   - [ ] 了解命名约定和代码模式

2. **开发中**
   - [ ] 遵守项目的分层架构（core/services/api/models 等）
   - [ ] 遵循命名规范（snake_case, PascalCase, kebab-case）
   - [ ] 新功能检查是否已有类似模块（避免重复）
   - [ ] 外部数据统一通过 `utils/stock_tool.py` 获取

3. **开发后**
   - [ ] 添加必要的测试文件
   - [ ] 更新相关文档
   - [ ] 检查路由/模型是否正确注册

## 快速参考

### 后端关键规范
- 使用 `uv` 管理依赖，不使用 pip
- 服务层单例模式：`get_xxx_service()` 工厂函数
- 外部数据：`utils/stock_tool.py`
- LLM 实例：`core/llm_factory.py`
- 新 API 需在 `api/__init__.py` 注册

### 前端关键规范
- 技术栈：Vite + React 18 + TypeScript + TailwindCSS 3 + Zustand
- 类型定义统一放在 `types/` 目录
- API 请求放在 `api/` 目录
- 组件放在 `components/` 按功能分子目录
- 工具函数检查 `utils/format.ts` 是否已有实现

## 更多信息

完整规则请阅读 `project-rule.md` 文件。
