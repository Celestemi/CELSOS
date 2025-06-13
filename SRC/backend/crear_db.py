import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    fullname TEXT
)
''')

conn.commit()
conn.close()

print("Base de datos creada correctamente con la tabla 'users'")
