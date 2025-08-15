import sqlite3, json, os

data_dir = os.path.dirname(__file__)
db_path = os.path.join(data_dir, 'aftersales.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 清空所有表，重建
for tbl in ["brands", "categories", "addresses", "users", "orders", "order_items", "logistics", "return_status", "refund_status"]:
    c.execute(f"DROP TABLE IF EXISTS {tbl}")

# 建表
c.execute('''CREATE TABLE IF NOT EXISTS brands (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, code TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS addresses (id INTEGER PRIMARY KEY AUTOINCREMENT, address TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    email TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    user_id INTEGER,
    status TEXT,
    amount REAL,
    address_id INTEGER,
    created_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')
c.execute('''CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, name TEXT, sku TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logistics (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, time TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS return_status (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, item_sku TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS refund_status (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, status TEXT)''')
conn.commit()

# 导入 brands
with open(os.path.join(data_dir, 'brands.json'), encoding='utf-8') as f:
    brands = json.load(f)
for b in brands:
    c.execute('INSERT OR IGNORE INTO brands (name) VALUES (?)', (b,))

# 导入 categories
with open(os.path.join(data_dir, 'categories.json'), encoding='utf-8') as f:
    categories = json.load(f)
for name, code in categories:
    c.execute('INSERT OR IGNORE INTO categories (name, code) VALUES (?, ?)', (name, code))

# 导入 addresses
with open(os.path.join(data_dir, 'addresses.json'), encoding='utf-8') as f:
    addresses = json.load(f)
for addr in addresses:
    c.execute('INSERT OR IGNORE INTO addresses (address) VALUES (?)', (addr,))

# 地址辅助函数
c.execute('SELECT id, address FROM addresses')
addr_map = {v: k for k, v in c.fetchall()}

# 导入 users
with open(os.path.join(data_dir, 'users.json'), encoding='utf-8') as f:
    users = json.load(f)
user_id_map = {}
for u in users:
    c.execute('INSERT INTO users (name, phone, email) VALUES (?, ?, ?)', (u['name'], u['phone'], u['email']))
    user_id_map[u['user_id']] = c.lastrowid
conn.commit()

# 导入 orders 和 order_items
with open(os.path.join(data_dir, 'orders.json'), encoding='utf-8') as f:
    orders = json.load(f)
for oid, o in orders.items():
    addr_id = addr_map.get(o['address'])
    user_id = user_id_map.get(o['user_id'])
    c.execute('INSERT OR IGNORE INTO orders (order_id, user_id, status, amount, address_id, created_at) VALUES (?, ?, ?, ?, ?, ?)',
              (oid, user_id, o['status'], o['amount'], addr_id, '2025-08-15'))
    for item in o['items']:
        c.execute('INSERT INTO order_items (order_id, name, sku) VALUES (?, ?, ?)', (oid, item['name'], item['sku']))

# 导入 logistics
with open(os.path.join(data_dir, 'logistics.json'), encoding='utf-8') as f:
    logistics = json.load(f)
for oid, logs in logistics.items():
    for log in logs:
        c.execute('INSERT INTO logistics (order_id, time, status) VALUES (?, ?, ?)', (oid, log['time'], log['status']))

# 导入 return_status
with open(os.path.join(data_dir, 'return_status.json'), encoding='utf-8') as f:
    return_status = json.load(f)
for k, status in return_status.items():
    # k 格式为 "(order_id, sku)"
    if k.startswith('('):
        parts = k[1:-1].split(', ')
        oid = parts[0].strip("'")
        sku = parts[1].strip("'")
        c.execute('INSERT INTO return_status (order_id, item_sku, status) VALUES (?, ?, ?)', (oid, sku, status))

# 导入 refund_status
with open(os.path.join(data_dir, 'refund_status.json'), encoding='utf-8') as f:
    refund_status = json.load(f)
for oid, status in refund_status.items():
    c.execute('INSERT INTO refund_status (order_id, status) VALUES (?, ?)', (oid, status))

conn.commit()
conn.close()
print('数据库初始化完成，数据已导入。')
