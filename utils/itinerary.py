import sqlite3
import os

class ItineraryManager:
    def __init__(self, db_path='data/travel.db'):
        """
        Initializes the ItineraryManager, connecting to the database and
        ensuring the 'trips' table exists.

        Args:
            db_path (str): The path to the SQLite database file.
        """
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._ensure_trips_table()

    def _get_db_connection(self):
        """Creates and returns a new database connection."""
        return sqlite3.connect(self.db_path)

    def _ensure_trips_table(self):
        """
        Checks if the 'trips' table exists in the database and creates it
        if it does not.
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def create_new_trip(self, name, start_date, end_date):
        """
        Adds a new trip to the 'trips' table.

        Args:
            name (str): The name of the trip.
            start_date (str): The start date of the trip (e.g., 'YYYY-MM-DD').
            end_date (str): The end date of the trip (e.g., 'YYYY-MM-DD').

        Returns:
            int: The ID of the newly created trip.
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO trips (name, start_date, end_date) VALUES (?, ?, ?)",
            (name, start_date, end_date)
        )
        conn.commit()
        trip_id = cursor.lastrowid
        conn.close()
        return trip_id

if __name__ == '__main__':
    # Example usage:
    manager = ItineraryManager()
    
    # Create a new trip
    new_trip_id = manager.create_new_trip("Kyoto Adventure", "2024-04-10", "2024-04-18")
    print(f"Successfully created a new trip with ID: {new_trip_id}")

    # Verify the trip was created by reading from the database
    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE id = ?", (new_trip_id,))
    trip = cursor.fetchone()
    conn.close()
    
    if trip:
        print(f"Verified trip from DB: {trip}")
    else:
        print("Could not verify the trip in the database.")