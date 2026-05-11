import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "database")
DB_PATH = os.path.join(DB_DIR, "travel.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _safe_add_column(cur, table, column, col_type, default=None):
    """Add a column to a table if it doesn't already exist."""
    try:
        if default is not None:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default}")
        else:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass  # Column already exists

def init_db():
    """Initialize database with tables strictly aligned to the UML ERD.
    Uses CREATE TABLE IF NOT EXISTS so data persists across restarts."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cur = conn.cursor()

    # Keep feedback for admin panel
    cur.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ERD: User
    cur.execute('''
        CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            email TEXT,
            password TEXT NOT NULL,
            budget REAL,
            travel_days INTEGER
        )
    ''')

    # ERD: Destination
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Destination (
            destination_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            average_cost REAL
        )
    ''')

    # ERD: Accommodation
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Accommodation (
            accommodation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL,
            rating REAL,
            location TEXT
        )
    ''')

    # ERD: TravelPlan
    cur.execute('''
        CREATE TABLE IF NOT EXISTS TravelPlan (
            plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            destination_id INTEGER,
            total_cost REAL,
            duration INTEGER,
            FOREIGN KEY(user_id) REFERENCES User(user_id),
            FOREIGN KEY(destination_id) REFERENCES Destination(destination_id)
        )
    ''')

    # ERD: Booking
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Booking (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            accommodation_id INTEGER,
            plan_id INTEGER,
            booking_date TEXT,
            stay_days INTEGER,
            FOREIGN KEY(user_id) REFERENCES User(user_id),
            FOREIGN KEY(accommodation_id) REFERENCES Accommodation(accommodation_id),
            FOREIGN KEY(plan_id) REFERENCES TravelPlan(plan_id)
        )
    ''')

    # ── New columns for enhanced features ──
    # User preferences
    _safe_add_column(cur, "User", "place_types", "TEXT")
    _safe_add_column(cur, "User", "season", "TEXT")

    # TravelPlan enhancements for history
    _safe_add_column(cur, "TravelPlan", "destination_name", "TEXT")
    _safe_add_column(cur, "TravelPlan", "interest", "TEXT")
    _safe_add_column(cur, "TravelPlan", "place_types", "TEXT")
    _safe_add_column(cur, "TravelPlan", "season", "TEXT")
    _safe_add_column(cur, "TravelPlan", "travel_mode", "TEXT")
    _safe_add_column(cur, "TravelPlan", "itinerary_json", "TEXT")
    _safe_add_column(cur, "TravelPlan", "start_date", "TEXT")
    _safe_add_column(cur, "TravelPlan", "end_date", "TEXT")
    _safe_add_column(cur, "TravelPlan", "created_at", "TIMESTAMP", "CURRENT_TIMESTAMP")

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")

def save_feedback(name, email, message):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO feedback (name, email, message) VALUES (?, ?, ?)", (name, email, message))
    conn.commit()
    conn.close()
    print(f"💾 Feedback saved: {name}")

# Seed dummy data for Destination and Accommodation
def seed_dummy_data():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Only seed if empty
    cur.execute("SELECT COUNT(*) FROM Destination")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO Destination (name, type, average_cost) VALUES (?, ?, ?)", [
            ("Paris", "City", 1500.0),
            ("Maldives", "Beach", 3000.0),
            ("Kyoto", "Heritage", 1200.0),
            ("Indore", "City", 200.0)
        ])
        
        cur.executemany("INSERT INTO Accommodation (name, price, rating, location) VALUES (?, ?, ?, ?)", [
            ("Le Meurice", 500.0, 4.8, "Paris"),
            ("Soneva Jani", 1200.0, 4.9, "Maldives"),
            ("Ritz-Carlton Kyoto", 400.0, 4.7, "Kyoto"),
            ("Marriott Indore", 100.0, 4.5, "Indore")
        ])
        conn.commit()
        print("✅ Seeded dummy Destination and Accommodation data.")
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_dummy_data()
