import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "database", "travel.db")

def check_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        print("--- Destination Table ---")
        cur.execute("SELECT * FROM Destination LIMIT 5")
        rows = cur.fetchall()
        for row in rows:
            print(dict(row))
            
        print("\n--- Table Names ---")
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        for t in tables:
            print(t['name'])
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
