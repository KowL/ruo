#!/usr/bin/env python3
"""
概念数据导入脚本
手动导入热门概念和概念股
"""
import sys
sys.path.insert(0, '/Volumes/mm/项目/ruo/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.concept import Concept, ConceptStock

# 数据库连接 (使用 docker 网络内的 postgres 服务)
DATABASE_URL = "postgresql://ruo_user:ruo_password@postgres:5432/ruo_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def import_concepts():
    db = SessionLocal()
    
    # 热门概念数据
    concepts_data = [
        {"name": "人工智能", "description": "AI、大模型、机器学习相关", "stocks": [("300033", "同花顺"), ("002230", "科大讯飞"), ("688981", "中芯国际")]},
        {"name": "新能源", "description": "光伏、风电、储能等清洁能源", "stocks": [("300750", "宁德时代"), ("002594", "比亚迪"), ("601012", "隆基绿能")]},
        {"name": "半导体", "description": "芯片设计、制造、封测", "stocks": [("688981", "中芯国际"), ("002371", "北方华创"), ("603501", "韦尔股份")]},
        {"name": "医药", "description": "创新药、医疗器械、生物制药", "stocks": [("600276", "恒瑞医药"), ("000538", "云南白药"), ("603259", "药明康德")]},
        {"name": "银行", "description": "商业银行、投资银行", "stocks": [("000001", "平安银行"), ("600036", "招商银行"), ("601398", "工商银行")]},
        {"name": "消费电子", "description": "手机、电脑、可穿戴设备", "stocks": [("002475", "立讯精密"), ("000725", "京东方A"), ("300433", "蓝思科技")]},
        {"name": "5G通信", "description": "5G基站、通信设备", "stocks": [("000063", "中兴通讯"), ("600498", "烽火通信"), ("300136", "信维通信")]},
        {"name": "云计算", "description": "云基础设施、SaaS服务", "stocks": [("000938", "中芯国际"), ("600570", "恒生电子"), ("300454", "深信服")]},
        {"name": "区块链", "description": "数字货币、区块链技术", "stocks": [("300386", "飞天诚信"), ("002177", "御银股份"), ("300468", "四方精创")]},
        {"name": "新能源汽车", "description": "电动车、充电桩", "stocks": [("002594", "比亚迪"), ("300750", "宁德时代"), ("601127", "赛力斯")]},
        {"name": "军工", "description": "航空航天、国防装备", "stocks": [("600893", "航发动力"), ("000768", "中航西飞"), ("600760", "中航沈飞")]},
        {"name": "白酒", "description": "高端白酒、区域白酒", "stocks": [("600519", "贵州茅台"), ("000858", "五粮液"), ("000568", "泸州老窖")]},
        {"name": "券商", "description": "证券经纪、投行", "stocks": [("300059", "东方财富"), ("600030", "中信证券"), ("601688", "华泰证券")]},
        {"name": "房地产", "description": "住宅开发、商业地产", "stocks": [("000002", "万科A"), ("600048", "保利发展"), ("001979", "招商蛇口")]},
        {"name": "光伏", "description": "光伏组件、逆变器", "stocks": [("601012", "隆基绿能"), ("600438", "通威股份"), ("688599", "天合光能")]},
        {"name": "锂电池", "description": "动力电池、储能电池", "stocks": [("300750", "宁德时代"), ("002074", "国轩高科"), ("300014", "亿纬锂能")]},
        {"name": "数据中心", "description": "IDC、服务器", "stocks": [("000938", "中芯国际"), ("603019", "中科曙光"), ("002335", "科华数据")]},
        {"name": "ChatGPT", "description": "大模型、AIGC应用", "stocks": [("300033", "同花顺"), ("002230", "科大讯飞"), ("300418", "昆仑万维")]},
        {"name": "机器人", "description": "工业机器人、服务机器人", "stocks": [("002008", "大族激光"), ("300124", "汇川技术"), ("002747", "埃斯顿")]},
        {"name": "芯片", "description": "集成电路设计制造", "stocks": [("688981", "中芯国际"), ("002156", "通富微电"), ("600584", "长电科技")]},
    ]
    
    count = 0
    stock_count = 0
    
    for concept_data in concepts_data:
        # 检查是否已存在
        existing = db.query(Concept).filter(Concept.name == concept_data["name"]).first()
        if existing:
            print(f"跳过已存在概念: {concept_data['name']}")
            continue
        
        # 创建概念
        concept = Concept(
            name=concept_data["name"],
            description=concept_data["description"]
        )
        db.add(concept)
        db.flush()  # 获取 ID
        count += 1
        
        # 添加概念股
        for symbol, name in concept_data["stocks"]:
            stock = ConceptStock(
                concept_id=concept.id,
                stock_symbol=symbol,
                stock_name=name
            )
            db.add(stock)
            stock_count += 1
    
    db.commit()
    db.close()
    
    print(f"✅ 导入完成: {count} 个概念, {stock_count} 只概念股")
    return count, stock_count

if __name__ == "__main__":
    import_concepts()
