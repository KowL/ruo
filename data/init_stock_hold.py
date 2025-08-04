import sqlite3

conn = sqlite3.connect('ruo.db')
cursor = conn.cursor()

# 创建 prices 表 (如果不存在)
cursor.execute('''CREATE TABLE IF NOT EXISTS stock_prices 
                  (stock TEXT, timestamp DATETIME, price REAL)''')

# 创建 portfolio 表 (如果不存在)
cursor.execute('''CREATE TABLE IF NOT EXISTS stock_hold 
                  (stock TEXT PRIMARY KEY, name TEXT, hold_num INTEGER, available INTEGER, cost REAL)''')

# 插入示例数据 (替换为您的实际数据)
example_data = [
    ('AAPL', '苹果', 100, 50, 150.0),  # AAPL: 持仓100股，可用50股，成本150 USD
    ('GOOGL', '谷歌', 200, 100, 120.0)  # GOOGL: 持仓200股，可用100股，成本120 USD
]
cursor.executemany("INSERT OR REPLACE INTO stock_hold (stock, name, hold_num, available, cost) VALUES (?, ?, ?, ?, ?)", example_data)

conn.commit()
conn.close()
print("Database initialized with example data.")
