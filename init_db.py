import sqlite3

# Connect to SQLite database
conn = sqlite3.connect("smartcart.db")

# Open schema.sql file
with open("schema.sql") as f:
    conn.executescript(f.read())

print("Database and tables created successfully!")

conn.close()
