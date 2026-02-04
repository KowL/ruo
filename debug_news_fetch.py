import sys
import os
import logging

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.tasks.news_fetch_tasks import fetch_cls_news_task, fetch_xueqiu_news_task

# Configure logging to see output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cls_fetch():
    logger.info("Testing CLS news fetch...")
    result = fetch_cls_news_task(limit=5)
    logger.info(f"CLS Result: {result}")

def test_xueqiu_fetch():
    logger.info("Testing Xueqiu news fetch...")
    result = fetch_xueqiu_news_task(limit=5)
    logger.info(f"Xueqiu Result: {result}")

if __name__ == "__main__":
    logger.info("Starting manual news fetch test")
    try:
        test_cls_fetch()
    except Exception as e:
        logger.error(f"CLS fetch failed: {e}")
    
    try:
        test_xueqiu_fetch()
    except Exception as e:
        logger.error(f"Xueqiu fetch failed: {e}")
