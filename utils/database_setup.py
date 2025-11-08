import sqlite3
import os

DB_DIR = os.path.join(os.getcwd(), "database")
DB_PATH = os.path.join(DB_DIR, "travel.db")

def init_db():
    """Initialize database and create feedback table."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def save_feedback(name, email, message):
    """Save feedback into database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO feedback (name, email, message) VALUES (?, ?, ?)", (name, email, message))
    conn.commit()
    conn.close()
    print(f"💾 Feedback saved: {name}")
