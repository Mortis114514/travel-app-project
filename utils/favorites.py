"""
Favorites management module
Handles CRUD operations for user favorites (restaurants, hotels, attractions)
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

# Database path (same as auth.py)
DB_PATH = './data/users.db'

@contextmanager
def get_favorites_db_connection():
    """Database connection context manager for favorites operations"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def add_favorite(
    user_id: int,
    item_type: str,
    item_id: int,
    item_name: str,
    item_data: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str]:
    """
    Add item to user's favorites

    Args:
        user_id: User ID from session
        item_type: 'restaurant', 'hotel', or 'attraction'
        item_id: ID of the item in respective database
        item_name: Display name of the item
        item_data: Optional metadata (rating, image, location, etc.)

    Returns:
        (success: bool, message: str)
    """
    try:
        with get_favorites_db_connection() as conn:
            cursor = conn.cursor()

            # Convert item_data dict to JSON string
            data_json = json.dumps(item_data) if item_data else None

            cursor.execute('''
                INSERT INTO favorites (user_id, item_type, item_id, item_name, item_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, item_type, item_id, item_name, data_json))

            conn.commit()
            return True, f"{item_name} added to favorites"

    except sqlite3.IntegrityError:
        # Already favorited (UNIQUE constraint violation)
        return False, f"{item_name} is already in your favorites"
    except Exception as e:
        return False, f"Failed to add favorite: {str(e)}"


def remove_favorite(
    user_id: int,
    item_type: str,
    item_id: int
) -> Tuple[bool, str]:
    """
    Remove item from user's favorites

    Args:
        user_id: User ID from session
        item_type: 'restaurant', 'hotel', or 'attraction'
        item_id: ID of the item

    Returns:
        (success: bool, message: str)
    """
    try:
        with get_favorites_db_connection() as conn:
            cursor = conn.cursor()

            # Get item name before deletion for message
            cursor.execute('''
                SELECT item_name FROM favorites
                WHERE user_id = ? AND item_type = ? AND item_id = ?
            ''', (user_id, item_type, item_id))

            result = cursor.fetchone()
            if not result:
                return False, "Item not found in favorites"

            item_name = result['item_name']

            # Delete the favorite
            cursor.execute('''
                DELETE FROM favorites
                WHERE user_id = ? AND item_type = ? AND item_id = ?
            ''', (user_id, item_type, item_id))

            conn.commit()
            return True, f"{item_name} removed from favorites"

    except Exception as e:
        return False, f"Failed to remove favorite: {str(e)}"


def toggle_favorite(
    user_id: int,
    item_type: str,
    item_id: int,
    item_name: str,
    item_data: Optional[Dict[str, Any]] = None
) -> Tuple[bool, bool, str]:
    """
    Toggle favorite status (add if not favorited, remove if already favorited)

    Args:
        user_id: User ID from session
        item_type: 'restaurant', 'hotel', or 'attraction'
        item_id: ID of the item
        item_name: Display name of the item
        item_data: Optional metadata

    Returns:
        (success: bool, is_now_favorited: bool, message: str)
    """
    # Check if already favorited
    if is_favorited(user_id, item_type, item_id):
        success, msg = remove_favorite(user_id, item_type, item_id)
        return success, False, msg
    else:
        success, msg = add_favorite(user_id, item_type, item_id, item_name, item_data)
        return success, True, msg


def is_favorited(
    user_id: int,
    item_type: str,
    item_id: int
) -> bool:
    """
    Check if an item is in user's favorites

    Args:
        user_id: User ID from session
        item_type: 'restaurant', 'hotel', or 'attraction'
        item_id: ID of the item

    Returns:
        True if favorited, False otherwise
    """
    try:
        with get_favorites_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM favorites
                WHERE user_id = ? AND item_type = ? AND item_id = ?
            ''', (user_id, item_type, item_id))

            return cursor.fetchone() is not None
    except Exception:
        return False


def get_user_favorites(
    user_id: int,
    item_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all favorites for a user, optionally filtered by type

    Args:
        user_id: User ID from session
        item_type: Optional filter ('restaurant', 'hotel', 'attraction')

    Returns:
        List of favorite items with metadata
    """
    try:
        with get_favorites_db_connection() as conn:
            cursor = conn.cursor()

            if item_type:
                cursor.execute('''
                    SELECT * FROM favorites
                    WHERE user_id = ? AND item_type = ?
                    ORDER BY created_at DESC
                ''', (user_id, item_type))
            else:
                cursor.execute('''
                    SELECT * FROM favorites
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))

            rows = cursor.fetchall()

            # Convert to list of dicts and parse JSON data
            favorites = []
            for row in rows:
                fav = dict(row)
                if fav['item_data']:
                    try:
                        fav['item_data'] = json.loads(fav['item_data'])
                    except json.JSONDecodeError:
                        fav['item_data'] = None
                favorites.append(fav)

            return favorites

    except Exception as e:
        print(f"Error fetching favorites: {e}")
        return []


def get_favorites_by_ids(
    user_id: int,
    item_type: str
) -> List[int]:
    """
    Get list of favorited item IDs for a specific type
    Useful for batch checking favorite states in list views

    Args:
        user_id: User ID from session
        item_type: 'restaurant', 'hotel', or 'attraction'

    Returns:
        List of item IDs that are favorited
    """
    try:
        with get_favorites_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT item_id FROM favorites
                WHERE user_id = ? AND item_type = ?
            ''', (user_id, item_type))

            return [row['item_id'] for row in cursor.fetchall()]
    except Exception:
        return []


def get_favorites_count(user_id: int) -> Dict[str, int]:
    """
    Get count of favorites by type for a user

    Args:
        user_id: User ID from session

    Returns:
        Dict with counts: {'restaurant': 5, 'hotel': 3, 'attraction': 8, 'total': 16}
    """
    try:
        with get_favorites_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT item_type, COUNT(*) as count
                FROM favorites
                WHERE user_id = ?
                GROUP BY item_type
            ''', (user_id,))

            counts = {
                'restaurant': 0,
                'hotel': 0,
                'attraction': 0,
                'total': 0
            }

            for row in cursor.fetchall():
                counts[row['item_type']] = row['count']
                counts['total'] += row['count']

            return counts
    except Exception:
        return {'restaurant': 0, 'hotel': 0, 'attraction': 0, 'total': 0}


def clear_user_favorites(user_id: int, item_type: Optional[str] = None) -> Tuple[bool, str]:
    """
    Clear all favorites for a user (optionally filtered by type)
    Useful for testing or user account management

    Args:
        user_id: User ID from session
        item_type: Optional filter ('restaurant', 'hotel', 'attraction')

    Returns:
        (success: bool, message: str)
    """
    try:
        with get_favorites_db_connection() as conn:
            cursor = conn.cursor()

            if item_type:
                cursor.execute('''
                    DELETE FROM favorites
                    WHERE user_id = ? AND item_type = ?
                ''', (user_id, item_type))
                msg = f"All {item_type} favorites cleared"
            else:
                cursor.execute('''
                    DELETE FROM favorites
                    WHERE user_id = ?
                ''', (user_id,))
                msg = "All favorites cleared"

            conn.commit()
            rows_deleted = cursor.rowcount

            if rows_deleted > 0:
                return True, f"{msg} ({rows_deleted} items removed)"
            else:
                return True, "No favorites to clear"

    except Exception as e:
        return False, f"Failed to clear favorites: {str(e)}"
