# ruo

基于AI Agents的个人资讯决策系统

## 项目简介
本项目旨在通过AI Agents帮助个人进行资讯收集、分析与决策，提升信息处理效率。

## 主要功能
- 资讯自动收集与聚合
- 智能分析与摘要
- 决策建议生成
- 支持自定义Agent扩展

## AI工作流
- RSS收集信息 → 聚合分析 → 分类整理 → 生成报告

## 技术栈
- Python 3.9+
- FastAPI
- OpenAI/LLM
- LangChain
- LangGraph
- nv（包管理）

## 安装依赖
```bash
nv install
```

## 运行项目
```bash
uvicorn main:app --reload
```

## 目录结构
- `main.py`：主入口
- `agents/`：Agent相关代码
- `services/`：服务与工具
- `data/`：数据存储

## 贡献
欢迎提交PR或Issue！ 