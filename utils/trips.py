"""
Trip management module
Handles CRUD operations for user trips and trip items
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

# Database path (same as auth.py and favorites.py)
DB_PATH = './data/users.db'

@contextmanager
def get_trips_db_connection():
    """Database connection context manager for trip operations"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_trip(
    user_id: int,
    trip_name: str,
    start_date: str,
    end_date: str,
    description: Optional[str] = None
) -> Tuple[bool, int, str]:
    """
    Create a new trip

    Args:
        user_id: User ID from session
        trip_name: Name of the trip
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        description: Optional trip description

    Returns:
        (success: bool, trip_id: int, message: str)
    """
    try:
        with get_trips_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trips (user_id, trip_name, start_date, end_date, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, trip_name, start_date, end_date, description))

            conn.commit()
            trip_id = cursor.lastrowid
            return True, trip_id, f"Trip '{trip_name}' created successfully"

    except Exception as e:
        return False, 0, f"Failed to create trip: {str(e)}"


def get_user_trips(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all trips for a user

    Args:
        user_id: User ID from session

    Returns:
        List of trip dictionaries
    """
    try:
        with get_trips_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM trips
                WHERE user_id = ?
                ORDER BY start_date DESC
            ''', (user_id,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error fetching trips: {e}")
        return []


def get_trip_by_id(trip_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single trip by ID

    Args:
        trip_id: Trip ID

    Returns:
        Trip dictionary or None
    """
    try:
        with get_trips_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM trips WHERE id = ?', (trip_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    except Exception as e:
        print(f"Error fetching trip: {e}")
        return None


def add_item_to_trip(
    trip_id: int,
    item_type: str,
    item_id: int,
    item_name: str,
    day_number: int,
    notes: Optional[str] = None,
    time: Optional[str] = None,
    cost: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Add an item (restaurant/hotel/attraction) to a trip

    Args:
        trip_id: Trip ID
        item_type: 'restaurant', 'hotel', or 'attraction'
        item_id: ID of the item
        item_name: Display name
        day_number: Which day of the trip (1, 2, 3, etc.)
        notes: Optional notes for this item
        time: Optional time for this item (HH:MM format)
        cost: Optional cost/budget for this item

    Returns:
        (success: bool, message: str)
    """
    try:
        with get_trips_db_connection() as conn:
            cursor = conn.cursor()

            # Get current max order for this day
            cursor.execute('''
                SELECT COALESCE(MAX(order_in_day), 0) as max_order
                FROM trip_items
                WHERE trip_id = ? AND day_number = ?
            ''', (trip_id, day_number))

            max_order = cursor.fetchone()['max_order']
            new_order = max_order + 1

            cursor.execute('''
                INSERT INTO trip_items (trip_id, item_type, item_id, item_name, day_number, order_in_day, notes, time, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trip_id, item_type, item_id, item_name, day_number, new_order, notes, time, cost))

            conn.commit()
            return True, f"{item_name} added to Day {day_number}"

    except Exception as e:
        return False, f"Failed to add item: {str(e)}"


def get_trip_items(trip_id: int) -> List[Dict[str, Any]]:
    """
    Get all items in a trip, organized by day

    Args:
        trip_id: Trip ID

    Returns:
        List of trip item dictionaries
    """
    try:
        with get_trips_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM trip_items
                WHERE trip_id = ?
                ORDER BY day_number, order_in_day
            ''', (trip_id,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error fetching trip items: {e}")
        return []


def remove_item_from_trip(item_id: int) -> Tuple[bool, str]:
    """
    Remove an item from a trip

    Args:
        item_id: Trip item ID

    Returns:
        (success: bool, message: str)
    """
    try:
        with get_trips_db_connection() as conn:
            cursor = conn.cursor()

            # Get item name before deletion
            cursor.execute('SELECT item_name FROM trip_items WHERE id = ?', (item_id,))
            result = cursor.fetchone()

            if not result:
                return False, "Item not found"

            item_name = result['item_name']

            cursor.execute('DELETE FROM trip_items WHERE id = ?', (item_id,))
            conn.commit()

            return True, f"{item_name} removed from trip"

    except Exception as e:
        return False, f"Failed to remove item: {str(e)}"


def delete_trip(trip_id: int) -> Tuple[bool, str]:
    """
    Delete a trip and all its items

    Args:
        trip_id: Trip ID

    Returns:
        (success: bool, message: str)
    """
    try:
        with get_trips_db_connection() as conn:
            cursor = conn.cursor()

            # Get trip name before deletion
            cursor.execute('SELECT trip_name FROM trips WHERE id = ?', (trip_id,))
            result = cursor.fetchone()

            if not result:
                return False, "Trip not found"

            trip_name = result['trip_name']

            # Delete trip (trip_items will be deleted automatically due to CASCADE)
            cursor.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
            conn.commit()

            return True, f"Trip '{trip_name}' deleted"

    except Exception as e:
        return False, f"Failed to delete trip: {str(e)}"


def update_trip(
    trip_id: int,
    trip_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    description: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Update trip details

    Args:
        trip_id: Trip ID
        trip_name: New trip name (optional)
        start_date: New start date (optional)
        end_date: New end date (optional)
        description: New description (optional)

    Returns:
        (success: bool, message: str)
    """
    try:
        with get_trips_db_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if trip_name is not None:
                updates.append('trip_name = ?')
                params.append(trip_name)

            if start_date is not None:
                updates.append('start_date = ?')
                params.append(start_date)

            if end_date is not None:
                updates.append('end_date = ?')
                params.append(end_date)

            if description is not None:
                updates.append('description = ?')
                params.append(description)

            if not updates:
                return False, "No updates provided"

            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(trip_id)

            query = f"UPDATE trips SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

            return True, "Trip updated successfully"

    except Exception as e:
        return False, f"Failed to update trip: {str(e)}"
