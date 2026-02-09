import sys
import os
import logging

# Add backend to path to allow imports from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('app.services.news_cleaner').setLevel(logging.DEBUG)

from app.tasks.news_fetch_tasks import fetch_xueqiu_news_task

if __name__ == "__main__":
    print(">>> Starting manual execution of fetch_xueqiu_news_task...")
    try:
        # Run the task synchronously
        result = fetch_xueqiu_news_task(limit=5)
        print("\n>>> Task Execution Completed")
        print(f"Result: {result}")
    except Exception as e:
        print(f"\n>>> Task Failed: {e}")
        import traceback
        traceback.print_exc()
