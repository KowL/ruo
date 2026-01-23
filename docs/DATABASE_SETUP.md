# PostgreSQL 数据库配置指南

## 📋 数据库信息

- **数据库名**: `ruo`
- **用户名**: `ruo`
- **密码**: `123456`
- **主机**: `localhost`
- **端口**: `5432`
- **连接字符串**: `postgresql://ruo:123456@localhost/ruo`

---

## 🚀 快速开始

### 方式一：使用脚本自动初始化（推荐）

```bash
# 1. 运行初始化脚本（需要 PostgreSQL 超级用户权限）
./scripts/init_db.sh

# 或者使用 brew services（macOS）
brew services start postgresql@15

# 然后运行脚本
psql postgres < scripts/init_db.sql
```

### 方式二：手动初始化

```bash
# 1. 启动 PostgreSQL（macOS）
brew services start postgresql@15

# 2. 连接到 PostgreSQL
psql postgres

# 3. 创建用户
CREATE USER ruo WITH PASSWORD '123456';

# 4. 创建数据库
CREATE DATABASE ruo OWNER ruo;

# 5. 授予权限
GRANT ALL PRIVILEGES ON DATABASE ruo TO ruo;

# 6. 退出
\q

# 7. 验证连接
psql -U ruo -d ruo -c "SELECT version();"
```

---

## 📊 创建数据库表

### 方式一：使用 Python 脚本

```bash
cd backend
python init_database.py --action create
```

### 方式二：使用 Alembic 迁移（推荐生产环境）

```bash
cd backend

# 1. 初始化 Alembic
alembic init alembic

# 2. 修改 alembic.ini 中的数据库连接
# sqlalchemy.url = postgresql://ruo:123456@localhost/ruo

# 3. 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 4. 应用迁移
alembic upgrade head
```

---

## 🗂️ 数据库表结构

创建后将包含以下 7 个表：

1. **users** - 用户表
   - 用户名、邮箱、密码等

2. **portfolios** - 持仓表
   - 股票代码、持仓数量、成本价、策略等

3. **trades** - 交易记录表
   - 买入/卖出记录、价格、数量等

4. **news** - 新闻表
   - 新闻标题、内容、来源、AI 分析结果等

5. **stocks** - 股票基础信息表
   - 股票代码、名称、板块、行业等

6. **stock_prices** - 股票价格历史数据表
   - K 线数据（开高低收、成交量等）

7. **analysis_reports** - AI 分析报告表
   - 分析结果、推荐操作、置信度等

---

## 🔍 常用数据库操作

### 连接数据库
```bash
psql -U ruo -d ruo
```

### 查看所有表
```sql
\dt
```

### 查看表结构
```sql
\d users
\d portfolios
```

### 查询数据
```sql
SELECT * FROM users;
SELECT * FROM portfolios WHERE symbol = '000001';
```

### 删除所有表（慎用！）
```bash
cd backend
python init_database.py --action drop
```

---

## 🐳 使用 Docker（可选）

如果不想本地安装 PostgreSQL，可以使用 Docker：

```bash
# 启动 PostgreSQL 容器
docker-compose up -d postgres

# 查看日志
docker-compose logs -f postgres

# 连接到容器中的数据库
docker exec -it ruo_postgres psql -U ruo -d ruo
```

---

## ⚠️ 常见问题

### 1. 连接被拒绝
```bash
# 检查 PostgreSQL 是否运行
brew services list

# 重启服务
brew services restart postgresql@15
```

### 2. 用户认证失败
```bash
# 检查 pg_hba.conf 文件
cat /opt/homebrew/var/postgresql@15/pg_hba.conf

# 确保包含以下行：
# local   all   all   trust
# host    all   all   127.0.0.1/32   trust
```

### 3. 端口被占用
```bash
# 检查端口占用
lsof -i :5432

# 修改配置使用其他端口
# 编辑 postgresql.conf: port = 5433
```

---

## 🔐 安全建议

**生产环境请务必：**

1. 修改默认密码为强密码
2. 限制数据库访问 IP
3. 启用 SSL 连接
4. 定期备份数据
5. 使用环境变量管理密码

```bash
# 修改密码
psql -U postgres -c "ALTER USER ruo WITH PASSWORD 'your_strong_password';"

# 更新 .env 文件
POSTGRES_PASSWORD=your_strong_password
```

---

## 📦 备份与恢复

### 备份数据库
```bash
pg_dump -U ruo ruo > backup_$(date +%Y%m%d).sql
```

### 恢复数据库
```bash
psql -U ruo ruo < backup_20260122.sql
```

---

## ✅ 验证安装

运行以下命令验证配置是否正确：

```bash
cd backend
python -c "from app.core.config import settings; print(f'Database URL: {settings.DATABASE_URL}')"
```

预期输出：
```
Database URL: postgresql://ruo:123456@localhost/ruo
```
