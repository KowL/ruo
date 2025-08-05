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
    ('002401', '中远海科', 2800, 2800, 22.023),
    ('300561', '汇科', 2800, 2800, 12.973),
    ('600438', '通威股份', 600, 600, 26.33)
]
cursor.executemany("INSERT OR REPLACE INTO stock_hold (stock, name, hold_num, available, cost) VALUES (?, ?, ?, ?, ?)", example_data)

conn.commit()
conn.close()
print("Database initialized with example data.")
