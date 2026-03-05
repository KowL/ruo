import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis
from redis.exceptions import ConnectionError

async def test_postgres():
    print(f"正在测试 PostgreSQL 连接: {settings.POSTGRES_HOST}")
    try:
        engine = sqlalchemy.create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            row = result.fetchone()
            print(f"✅ PostgreSQL 连接成功: {row[0]}")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        return False

def test_redis():
    print(f"正在测试 Redis 连接: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    try:
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        ping = r.ping()
        if ping:
            print("✅ Redis 连接成功: PONG")
            return True
    except ConnectionError as e:
        print(f"❌ Redis 连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ Redis 发生意外错误: {e}")
        return False

async def main():
    print("=== 开始后端连接测试 ===")
    print(f"当前配置:")
    print(f" - POSTGRES_HOST: {settings.POSTGRES_HOST}")
    print(f" - REDIS_HOST: {settings.REDIS_HOST}")
    print(f" - DATABASE_URL: {settings.DATABASE_URL}")
    print("-" * 30)
    
    pg_ok = await test_postgres()
    rd_ok = test_redis()
    
    print("-" * 30)
    if pg_ok and rd_ok:
        print("🎉 所有核心连接测试通过！")
    else:
        print("⚠️ 部分连接测试未通过，请检查服务状态或配置。")

if __name__ == "__main__":
    asyncio.run(main())
