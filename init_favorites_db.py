"""
Initialize favorites table in users.db
Run this once before using the favorites system

This script creates the favorites table with proper schema and indexes
for efficient querying of user favorites (restaurants, hotels, attractions)
"""
import sqlite3
import os

DB_PATH = os.path.join('data', 'users.db')

def init_favorites_table():
    """Create favorites table with proper schema and indexes"""

    if not os.path.exists('data'):
        os.makedirs('data')
        print("Created 'data' directory")

    if not os.path.exists(DB_PATH):
        print(f"Warning: {DB_PATH} does not exist. It will be created.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create favorites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_type TEXT NOT NULL CHECK(item_type IN ('restaurant', 'hotel', 'attraction')),
                item_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                item_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, item_type, item_id)
            )
        ''')
        print("[OK] Favorites table created successfully")

        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_favorites_user
            ON favorites(user_id)
        ''')
        print("[OK] Index idx_favorites_user created")

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_favorites_user_type
            ON favorites(user_id, item_type)
        ''')
        print("[OK] Index idx_favorites_user_type created")

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_favorites_lookup
            ON favorites(user_id, item_type, item_id)
        ''')
        print("[OK] Index idx_favorites_lookup created")

        conn.commit()
        print("\n[SUCCESS] Favorites table initialized successfully!")

        # Check if table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorites'")
        if cursor.fetchone():
            print("[OK] Favorites table exists in database")

            # Show table schema
            cursor.execute("PRAGMA table_info(favorites)")
            columns = cursor.fetchall()
            print("\nTable Schema:")
            print("-" * 60)
            for col in columns:
                print(f"  {col[1]:<15} {col[2]:<10} {'NOT NULL' if col[3] else ''}")
            print("-" * 60)

    except sqlite3.Error as e:
        print(f"[ERROR] Error creating favorites table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Favorites Database Initialization")
    print("=" * 60)
    print(f"Database: {DB_PATH}\n")

    init_favorites_table()

    print("\n" + "=" * 60)
    print("Initialization complete!")
    print("=" * 60)
