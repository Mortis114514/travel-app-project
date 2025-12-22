"""
Migration script to add 'cost' column to trip_items table
Run this once to update your database schema
"""
import sqlite3

DB_PATH = './data/users.db'

def add_cost_column():
    """Add cost column to trip_items table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(trip_items)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'cost' in columns:
            print("[OK] 'cost' column already exists in trip_items table")
        else:
            # Add the column
            cursor.execute("ALTER TABLE trip_items ADD COLUMN cost REAL")
            conn.commit()
            print("[OK] Successfully added 'cost' column to trip_items table")

        conn.close()

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    add_cost_column()
