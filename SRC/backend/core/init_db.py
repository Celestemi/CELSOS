import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def init_db():
    # Elimina la base de datos si ya existe (opcional)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Crea la tabla de usuarios correctamente
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT NOT NULL,
        fullname TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("✅ Base de datos inicializada correctamente.")

