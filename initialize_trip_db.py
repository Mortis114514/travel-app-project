
import sqlite3

DATABASE_PATH = 'data/travel.db'

def create_tables():
    """
    Creates the 'trips' and 'activities' tables in the database if they don't exist.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create trips table to store general trip information
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        trip_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # Create activities table for the itinerary
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id INTEGER NOT NULL,
        day INTEGER NOT NULL,
        start_time TEXT NOT NULL, -- Stored as 'HH:MM'
        end_time TEXT NOT NULL,   -- Stored as 'HH:MM'
        location_name TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (trip_id) REFERENCES trips (id)
    )
    """)

    print("Tables 'trips' and 'activities' created successfully or already exist.")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
