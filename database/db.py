import sqlite3
from config.settings import DATABASE_PATH
def get_connection():
    return sqlite3.connect(DATABASE_PATH)
