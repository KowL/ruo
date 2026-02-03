"""
数据库初始化脚本
Database Initialization Script
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import Base, engine, init_db
from app.models import User, Portfolio, Trade, News, Stock


def create_tables():
    """创建所有数据库表"""
    print("🔧 开始创建数据库表...")

    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功！")

        # 打印创建的表
        print("\n📊 已创建的表:")
        for table in Base.metadata.sorted_tables:
            print(f"   - {table.name}")

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        raise


def drop_all_tables():
    """删除所有表（慎用！）"""
    print("⚠️  警告：即将删除所有数据库表...")
    confirm = input("确认删除？(yes/no): ")

    if confirm.lower() == 'yes':
        Base.metadata.drop_all(bind=engine)
        print("✅ 所有表已删除")
    else:
        print("❌ 操作已取消")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument(
        '--action',
        choices=['create', 'drop'],
        default='create',
        help='操作类型: create(创建表) 或 drop(删除表)'
    )

    args = parser.parse_args()

    if args.action == 'create':
        create_tables()
    elif args.action == 'drop':
        drop_all_tables()
