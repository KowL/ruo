import sys
import os
sys.path.append(os.getcwd())

from app.tasks.stock_tasks import sync_stocks_task

if __name__ == "__main__":
    print("Triggering sync_stocks_task...")
    result = sync_stocks_task()
    print(f"Result: {result}")
