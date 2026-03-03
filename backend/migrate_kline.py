"""
K线数据表迁移脚本
创建kline_data表
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy import inspect
from app.core.config import settings
from app.core.database import Base, engine
from app.models.kline import KLineData


def migrate_kline_table():
    """创建K线数据表"""
    print("🔧 开始创建K线数据表...")
    
    try:
        # 使用SQLAlchemy创建表
        Base.metadata.create_all(bind=engine, tables=[KLineData.__table__])
        print("✅ K线数据表创建成功！")
        
        # 验证表是否创建
        from app.models.kline import KLineData
        inspector = inspect(engine)
        if inspector.has_table('kline_data'):
            print("✅ 验证通过：kline_data表已存在")
        else:
            print("⚠️ 验证失败：kline_data表未找到")
                
    except Exception as e:
        print(f"❌ 创建K线数据表失败: {e}")
        raise


if __name__ == "__main__":
    migrate_kline_table()
