import sqlite3
from typing import List, Dict
import hashlib

DB_PATH = "umpire_data.db"

def _get_connection():
    """Helper to return a configured SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initializes the database and seeds it with mock data, including passwords."""
    conn = _get_connection()
    cursor = conn.cursor()

    # Create Umpires table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS umpires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE COLLATE NOCASE NOT NULL,
            phone_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            available BOOLEAN NOT NULL,
            level TEXT NOT NULL,
            pay_rate REAL NOT NULL,
            registration_expiry TEXT NOT NULL,
            background_check_expiry TEXT NOT NULL,
            rating INTEGER DEFAULT 0,
            notes TEXT DEFAULT ''
        )
    ''')

    # Create Games table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            location TEXT NOT NULL,
            umpire_id INTEGER,
            status TEXT DEFAULT 'Scheduled',
            score TEXT DEFAULT NULL,
            game_type TEXT DEFAULT 'League',
            field_name TEXT DEFAULT '',
            FOREIGN KEY (umpire_id) REFERENCES umpires (id)
        )
    ''')

    # Migrations
    try:
        cursor.execute("ALTER TABLE umpires ADD COLUMN rating INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE umpires ADD COLUMN notes TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE games ADD COLUMN game_type TEXT DEFAULT 'League'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE games ADD COLUMN field_name TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass


    # Seed data if empty
    cursor.execute("SELECT COUNT(*) FROM umpires")
    if cursor.fetchone()[0] == 0:
        default_pw = hash_password("umpire123")
        cursor.executemany('''
            INSERT INTO umpires (name, phone_number, password_hash, available, level, pay_rate, registration_expiry, background_check_expiry, rating, notes) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            ("John Doe", "+15551234567", default_pw, True, "Senior", 65.0, "2027-01-01", "2027-05-15", 5, "Great umpire."), 
            ("Jane Smith", "+15559876543", default_pw, True, "Junior", 45.0, "2030-01-01", "2030-12-01", 4, ""), 
            ("Bob Johnson", "+15555555555", default_pw, False, "Senior", 65.0, "2027-01-01", "2027-06-01") 
        ])

    cursor.execute("SELECT COUNT(*) FROM games")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO games (date, time, location, umpire_id) VALUES (?, ?, ?, ?)
        ''', [
            ("2026-07-20", "18:00", "Field A", 1),
            ("2026-07-21", "14:00", "Field B", None),
            ("2026-07-22", "10:00", "Field C", None)
        ])

    conn.commit()
    conn.close()

def execute_query(query: str, params: tuple = ()) -> List[Dict]:
    """Helper to execute a read query and return a list of dictionaries."""
    conn = _get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def execute_write(query: str, params: tuple = ()):
    """Helper to execute an insert/update/delete query."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rowcount = cursor.rowcount
    conn.commit()
    conn.close()
    return rowcount

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded.")
