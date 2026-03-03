"""
批量新闻 AI 分析脚本
用于批量处理存量新闻的情绪分析
"""
import os
import sys
import time
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.services.ai_analysis import AIAnalysisService
from app.models.news import News
from sqlalchemy import func

def batch_analyze_news(batch_size=100, max_news=None):
    """
    批量分析新闻
    
    Args:
        batch_size: 每批处理数量
        max_news: 最大处理数量 (None=全部)
    """
    db = SessionLocal()
    
    try:
        # 统计待分析的新闻
        total_query = db.query(News).filter(News.ai_analysis == None)
        total_pending = total_query.count()
        
        if max_news:
            total_pending = min(total_pending, max_news)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始批量分析: 共 {total_pending} 条新闻待分析")
        
        service = AIAnalysisService(db)
        
        success = 0
        failed = 0
        skip = 0
        
        # 分批处理
        for offset in range(0, total_pending, batch_size):
            batch = total_query.offset(offset).limit(batch_size).all()
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 处理批次 {offset//batch_size + 1}/{(total_pending-1)//batch_size + 1} (共 {len(batch)} 条)")
            
            for news in batch:
                # 跳过已分析的（防止重复）
                if news.ai_analysis:
                    skip += 1
                    continue
                
                try:
                    result = service.analyze_news(news.id)
                    if result:
                        success += 1
                        label = result.get('sentiment_label', '?')
                        summary = result.get('ai_summary', '')[:30]
                        print(f"  ✓ ID:{news.id} [{label}] {summary}...")
                    else:
                        failed += 1
                        print(f"  ✗ ID:{news.id} - 返回空")
                        
                except Exception as e:
                    failed += 1
                    print(f"  ✗ ID:{news.id} - 错误: {str(e)[:50]}")
                
                # 控制频率
                time.sleep(0.3)
            
            # 每批处理完打印进度
            print(f"  进度: 成功 {success}, 失败 {failed}, 跳过 {skip}")
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 批量分析完成!")
        print(f"  总计: 成功 {success}, 失败 {failed}, 跳过 {skip}")
        
        return {
            'success': success,
            'failed': failed,
            'skip': skip
        }
        
    except Exception as e:
        print(f"批量分析失败: {e}")
        return None
    finally:
        db.close()


if __name__ == '__main__':
    # 解析参数
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    max_news = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    print("=" * 60)
    print("批量新闻 AI 分析工具")
    print("=" * 60)
    
    result = batch_analyze_news(batch_size=batch_size, max_news=max_news)
    
    if result:
        print("\n分析完成!")
        sys.exit(0)
    else:
        print("\n分析失败!")
        sys.exit(1)
