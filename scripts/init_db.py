#!/usr/bin/env python3
"""
PostgreSQL 数据库初始化脚本 - Python 版本
适用于所有平台，无需 shell 环境
"""
import subprocess
import sys
import os


def run_sql(sql, database='postgres', user='ruo', password='123456'):
    """执行 SQL 命令"""
    env = os.environ.copy()
    env['PGPASSWORD'] = password

    try:
        result = subprocess.run(
            ['psql', '-U', user, '-d', database, '-c', sql],
            capture_output=True,
            text=True,
            env=env
        )
        return result.returncode == 0, result.stdout, result.stderr
    except FileNotFoundError:
        print("❌ 错误: 找不到 psql 命令，请确保已安装 PostgreSQL")
        sys.exit(1)


def init_database():
    """初始化数据库"""
    print("🔧 开始初始化 PostgreSQL 数据库...\n")

    # 1. 创建用户（使用默认超级用户）
    print("📝 创建数据库用户 ruo...")
    success, stdout, stderr = run_sql(
        "CREATE USER ruo WITH PASSWORD '123456';",
        user=os.getenv('USER', 'postgres'),
        password=''
    )

    if success or 'already exists' in stderr:
        print("✅ 用户已就绪")
    else:
        print(f"⚠️  警告: {stderr.strip()}")

    # 2. 创建数据库
    print("📝 创建数据库 ruo...")
    success, stdout, stderr = run_sql(
        "CREATE DATABASE ruo OWNER ruo;",
        user=os.getenv('USER', 'postgres'),
        password=''
    )

    if success or 'already exists' in stderr:
        print("✅ 数据库已就绪")
    else:
        print(f"⚠️  警告: {stderr.strip()}")

    # 3. 授予权限
    print("🔑 授予数据库权限...")
    success, stdout, stderr = run_sql(
        "GRANT ALL PRIVILEGES ON DATABASE ruo TO ruo;",
        user=os.getenv('USER', 'postgres'),
        password=''
    )

    if success:
        print("✅ 权限授予成功")

    # 4. 授予 schema 权限
    print("🔑 授予 schema 权限...")
    success, stdout, stderr = run_sql(
        "GRANT ALL ON SCHEMA public TO ruo;",
        database='ruo',
        user='ruo',
        password='123456'
    )

    if success:
        print("✅ Schema 权限授予成功")

    # 5. 验证连接
    print("\n✅ 验证数据库连接...")
    success, stdout, stderr = run_sql(
        "SELECT 'Database connection successful!' AS status;",
        database='ruo',
        user='ruo',
        password='123456'
    )

    if success:
        print("✅ 数据库配置成功！\n")
        print("━" * 50)
        print("📊 数据库信息")
        print("━" * 50)
        print("   数据库名: ruo")
        print("   用户名:   ruo")
        print("   密码:     123456")
        print("   主机:     localhost")
        print("   端口:     5432")
        print("")
        print("🔗 连接字符串:")
        print("   postgresql://ruo:123456@localhost/ruo")
        print("━" * 50)
        print("\n📝 下一步:")
        print("   cd backend")
        print("   python init_database.py --action create\n")
        return True
    else:
        print(f"❌ 连接失败: {stderr.strip()}")
        print("\n💡 故障排查:")
        print("   1. 检查 PostgreSQL 是否运行")
        print("   2. 检查用户密码是否正确")
        print("   3. 尝试手动连接: psql -U ruo -d ruo")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
