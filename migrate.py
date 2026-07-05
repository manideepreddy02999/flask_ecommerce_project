import re
with open('app.py', 'r') as f:
    code = f.read()

# 1. Replace import mysql.connector
code = code.replace('import mysql.connector', 'import sqlite3')

# 2. Replace get_db
old_get_db = '''def get_db():
    connection = mysql.connector.connect(
        host=app.config['DB_HOST'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        database=app.config['DB_NAME']
    )
    return connection'''

new_get_db = '''def get_db():
    connection = sqlite3.connect("smartcart.db")
    connection.row_factory = sqlite3.Row
    return connection'''
code = code.replace(old_get_db, new_get_db)

# 3. Replace cursor(dictionary=True) with cursor()
code = code.replace('cursor = conn.cursor(dictionary=True)', 'cursor = conn.cursor()')

# 4. Remove CREATE TABLE blocks inside /verify-payment
create_orders = '''        # Create tables if not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                razorpay_order_id VARCHAR(100),
                razorpay_payment_id VARCHAR(100),
                amount DECIMAL(10,2),
                payment_status VARCHAR(30),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT PRIMARY KEY AUTO_INCREMENT,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                product_name VARCHAR(200),
                quantity INT,
                price DECIMAL(10,2),
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)'''

# If exact match fails, let's just do regex
code = re.sub(r'        # Create tables if not exist.*?        \"\"\"\)', '', code, flags=re.DOTALL)

# 5. Remove ALTER TABLE users ADD COLUMN address TEXT;
alter_users = '''    # Check if address column exists, if not add it
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN address TEXT;")
        conn.commit()
    except:
        pass # Column already exists'''
code = code.replace(alter_users, '')

# 6. Replace %s with ? only in SQL queries (ignoring logger and str%)
# Let's find all cursor.execute() calls and replace %s inside them.
def replace_sql_params(match):
    return match.group(0).replace('%s', '?')

code = re.sub(r'cursor\.execute\([\s\S]*?\)', replace_sql_params, code)

# Note: query += " AND name LIKE %s"
# query += " AND category = %s"
# These are outside cursor.execute, let's fix them explicitly:
code = code.replace('query += " AND name LIKE %s"', 'query += " AND name LIKE ?"')
code = code.replace('query += " AND category = %s"', 'query += " AND category = ?"')

# Write back
with open('app.py', 'w') as f:
    f.write(code)

print('app.py updated.')
