-- PostgreSQL 数据库初始化 SQL 脚本

-- 1. 创建用户
CREATE USER ruo WITH PASSWORD '123456';

-- 2. 创建数据库
CREATE DATABASE ruo OWNER ruo;

-- 3. 授予权限
GRANT ALL PRIVILEGES ON DATABASE ruo TO ruo;

-- 4. 连接到新数据库
\c ruo

-- 5. 授予 schema 权限
GRANT ALL ON SCHEMA public TO ruo;

-- 提示
SELECT 'Database setup completed successfully!' AS status;
