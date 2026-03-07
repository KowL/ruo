import sys
import os
import logging
import argparse

# Set environment variables for local execution
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
os.environ['DATABASE_URL'] = 'postgresql://ruo:1234567@localhost:5432/ruo'
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/1'
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'

# Clear all proxies
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(key, None)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from app.tasks.market_price_tasks import (
    sync_daily_price_task,
    sync_weekly_price_task,
    sync_monthly_price_task,
    sync_historical_price_task
)

def main():
    parser = argparse.ArgumentParser(description='同步行情数据到ruo数据库')
    parser.add_argument('--mode', choices=['daily', 'weekly', 'monthly', 'historical'], 
                        default='daily',
                        help='同步模式: daily=今日日线, weekly=本周周线, monthly=本月月线, historical=近10年全量')
    
    args = parser.parse_args()
    
    print(f">>> 开始同步行情数据 [模式: {args.mode}]...")
    
    try:
        if args.mode == 'daily':
            result = sync_daily_price_task()
        elif args.mode == 'weekly':
            result = sync_weekly_price_task()
        elif args.mode == 'monthly':
            result = sync_monthly_price_task()
        elif args.mode == 'historical':
            print(">>> 注意：历史数据同步需要较长时间（约数小时），每50只股票会休息30秒...")
            result = sync_historical_price_task()
        
        print(f"\n>>> 同步完成")
        print(f"结果: {result}")
        
    except Exception as e:
        print(f"\n>>> 同步失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
