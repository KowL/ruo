import sys
import os
import logging

# Set environment variables for local execution (connecting to Docker ports)
os.environ['DATABASE_URL'] = 'postgresql://ruo_user:ruo_password@localhost:5432/ruo_db'
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/1'
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'

# Add backend to path to allow imports from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Keep debug logging for news_cleaner
logging.getLogger('app.services.news_cleaner').setLevel(logging.DEBUG)

from app.tasks.news_fetch_tasks import fetch_xueqiu_news_task

if __name__ == "__main__":
    print(">>> Starting manual execution of fetch_xueqiu_news_task (Local Config)...")
    try:
        # Run the task synchronously
        result = fetch_xueqiu_news_task(limit=5)
        print("\n>>> Task Execution Completed")
        print(f"Result: {result}")
    except Exception as e:
        print(f"\n>>> Task Failed: {e}")
        import traceback
        traceback.print_exc()
