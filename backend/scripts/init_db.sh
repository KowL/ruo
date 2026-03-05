#!/bin/bash
# PostgreSQL 数据库初始化脚本 - 改进版

set -e  # 遇到错误立即退出

echo "🔧 开始初始化 PostgreSQL 数据库..."
echo ""

# 检测 PostgreSQL 用户
if id "postgres" &>/dev/null; then
    PGUSER="postgres"
elif whoami | grep -q "^postgres$"; then
    PGUSER=$(whoami)
else
    PGUSER=$(whoami)
fi

echo "📝 使用用户: $PGUSER"
echo ""

# 方式一：使用当前用户（macOS Homebrew 安装方式）
echo "=== 方式一：使用当前用户 ==="

# 1. 创建数据库用户
echo "📝 创建数据库用户 ruo..."
psql postgres -c "CREATE USER ruo WITH PASSWORD '123456';" 2>/dev/null && echo "✅ 用户创建成功" || echo "ℹ️  用户已存在，跳过创建"

# 2. 创建数据库
echo "📝 创建数据库 ruo..."
psql postgres -c "CREATE DATABASE ruo OWNER ruo;" 2>/dev/null && echo "✅ 数据库创建成功" || echo "ℹ️  数据库已存在，跳过创建"

# 3. 授予权限
echo "🔑 授予用户权限..."
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE ruo TO ruo;" && echo "✅ 权限授予成功"

# 4. 连接到 ruo 数据库并授予 schema 权限
echo "🔑 授予 schema 权限..."
psql ruo -c "GRANT ALL ON SCHEMA public TO ruo;" 2>/dev/null || echo "ℹ️  Schema 权限已存在"

# 5. 验证连接
echo ""
echo "✅ 验证数据库连接..."
if psql -U ruo -d ruo -c "SELECT 'Database connection successful!' AS status;" 2>/dev/null; then
    echo "✅ 数据库配置成功！"
else
    echo "❌ 连接失败，请检查配置"
    echo ""
    echo "💡 提示：如果连接失败，请尝试以下命令："
    echo "   export PGPASSWORD='123456'"
    echo "   psql -U ruo -d ruo"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 数据库信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   数据库名: ruo"
echo "   用户名:   ruo"
echo "   密码:     123456"
echo "   主机:     localhost"
echo "   端口:     5432"
echo ""
echo "🔗 连接字符串:"
echo "   postgresql://ruo:123456@localhost/ruo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 下一步："
echo "   cd backend"
echo "   python init_database.py --action create"
echo ""
