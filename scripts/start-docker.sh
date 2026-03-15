#!/bin/bash
# Docker 部署启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 复制Docker环境配置
cp .env.docker .env.docker.local

echo "使用Docker环境配置启动..."
docker-compose --env-file .env.docker.local up -d

echo ""
echo "服务启动完成！"
echo "- 后端: http://localhost:8000"
echo "- 前端: http://localhost:3000"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose --env-file .env.docker.local down"
