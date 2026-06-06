import sqlite3

DATABASE_PATH = "database/stock.db"

with open(
    "database/schema.sql",
    "r"
) as f:
    schema = f.read()

conn = sqlite3.connect(
    DATABASE_PATH
)

conn.executescript(schema)

conn.commit()

conn.close()

print(
    "Database created successfully."
)