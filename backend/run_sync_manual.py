import sys
import os
from pathlib import Path

# Ensure app is in python path
sys.path.insert(0, os.getcwd())

try:
    from app.tasks.stock_tasks import sync_stocks_task
    import time
    max_retries = 3
    for i in range(max_retries):
        print(f"Attempt {i+1}/{max_retries} to run sync_stocks_task...")
        result = sync_stocks_task()
        if result.get('status') == 'success':
            print("-" * 30)
            print(f"Task finished successfully.")
            print(f"Result: {result}")
            print("-" * 30)
            break
        else:
            print(f"Attempt {i+1} failed: {result.get('error')}")
            if i < max_retries - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("All attempts failed.")

except Exception as e:
    print(f"Error running task: {e}")
    import traceback
    traceback.print_exc()
