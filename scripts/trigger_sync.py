import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Force localhost connection when running from script
os.environ["DATABASE_URL"] = "postgresql://ruo_user:ruo_password@localhost:5432/ruo_db"

from app.tasks.stock_tasks import sync_stocks_task

if __name__ == "__main__":
    print("Triggering sync_stocks_task...")
    result = sync_stocks_task()
    print(f"Result: {result}")
