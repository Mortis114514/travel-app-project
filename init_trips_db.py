"""
Initialize trips database tables
Run this once to create the necessary tables for trip planning
"""
import sqlite3
from pathlib import Path

DB_PATH = './data/users.db'  # Store trips with user data

def init_trips_tables():
    """Create trips and trip_items tables"""

    # Ensure data directory exists
    Path('./data').mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create trips table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            trip_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # Create trip_items table (places added to trip)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trip_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            item_type TEXT NOT NULL CHECK(item_type IN ('restaurant', 'hotel', 'attraction')),
            item_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            day_number INTEGER NOT NULL,
            order_in_day INTEGER DEFAULT 0,
            notes TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE CASCADE
        )
    ''')

    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trip_items_trip ON trip_items(trip_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trip_items_day ON trip_items(trip_id, day_number)')

    conn.commit()
    conn.close()

    print("[SUCCESS] Trips database tables created successfully!")
    print(f"   Location: {DB_PATH}")
    print("   Tables: trips, trip_items")

if __name__ == '__main__':
    init_trips_tables()
