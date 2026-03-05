import sys
import os

# Set environment variables for local execution
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
os.environ['DATABASE_URL'] = 'postgresql://ruo:1234567@localhost:5432/ruo'

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check if column exists
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='stocks' AND column_name='sector'
    """))
    if result.fetchone():
        print('sector column already exists')
    else:
        conn.execute(text('ALTER TABLE stocks ADD COLUMN sector VARCHAR(50)'))
        conn.commit()
        print('sector column added successfully')
