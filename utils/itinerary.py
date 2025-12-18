
import sqlite3
from datetime import time

DATABASE_PATH = 'data/travel.db'

class ItineraryManager:
    """
    Manages itinerary data for a specific trip by interacting with the SQLite database.
    """
    def __init__(self, trip_id: int):
        """
        Initializes the manager for a specific trip.

        Args:
            trip_id: The ID of the trip to manage.
        """
        self.trip_id = trip_id
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.conn.cursor()

    def _time_str_to_obj(self, time_str: str) -> time:
        """Converts a 'HH:MM' string to a datetime.time object."""
        try:
            return time.fromisoformat(time_str)
        except (ValueError, TypeError):
            raise ValueError("Time must be in 'HH:MM' format.")

    def _check_overlap(self, day: int, new_start: time, new_end: time) -> bool:
        """
        Checks for time overlap with existing activities for a given day.

        Args:
            day: The day number of the itinerary.
            new_start: The start time of the new activity.
            new_end: The end time of the new activity.

        Returns:
            True if there is an overlap, False otherwise.
        """
        self.cursor.execute(
            "SELECT start_time, end_time FROM activities WHERE trip_id = ? AND day = ?",
            (self.trip_id, day)
        )
        activities = self.cursor.fetchall()

        for activity in activities:
            existing_start = self._time_str_to_obj(activity[0])
            existing_end = self._time_str_to_obj(activity[1])

            # Overlap condition: (StartA < EndB) and (EndA > StartB)
            if new_start < existing_end and new_end > existing_start:
                return True
        return False

    def add_activity(self, day: int, time_slot: tuple[str, str], location_name: str, notes: str = "") -> int:
        """
        Adds a new activity to the itinerary after checking for overlaps.

        Args:
            day: The day number (e.g., 1, 2).
            time_slot: A tuple containing start and end time strings ('HH:MM', 'HH:MM').
            location_name: The name of the location or activity.
            notes: Optional notes for the activity.

        Returns:
            The ID of the newly created activity.
        
        Raises:
            ValueError: If the time slot overlaps with an existing activity.
        """
        start_time_str, end_time_str = time_slot
        start_time_obj = self._time_str_to_obj(start_time_str)
        end_time_obj = self._time_str_to_obj(end_time_str)

        if start_time_obj >= end_time_obj:
            raise ValueError("End time must be after start time.")

        if self._check_overlap(day, start_time_obj, end_time_obj):
            raise ValueError(f"Time slot {start_time_str}-{end_time_str} on day {day} overlaps with an existing activity.")

        self.cursor.execute(
            """
            INSERT INTO activities (trip_id, day, start_time, end_time, location_name, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (self.trip_id, day, start_time_str, end_time_str, location_name, notes)
        )
        self.conn.commit()
        activity_id = self.cursor.lastrowid
        return activity_id

    def get_day_itinerary(self, day: int) -> list[dict]:
        """
        Retrieves all activities for a specific day, sorted by start time.

        Args:
            day: The day number.

        Returns:
            A list of activity dictionaries.
        """
        self.cursor.execute(
            "SELECT id, start_time, end_time, location_name, notes FROM activities WHERE trip_id = ? AND day = ? ORDER BY start_time",
            (self.trip_id, day)
        )
        activities = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in activities]

    def get_full_itinerary(self) -> dict[int, list[dict]]:
        """
        Retrieves the entire itinerary for the trip, organized by day.

        Returns:
            A dictionary where keys are day numbers and values are lists of activities.
        """
        self.cursor.execute(
            "SELECT day, id, start_time, end_time, location_name, notes FROM activities WHERE trip_id = ? ORDER BY day, start_time",
            (self.trip_id,)
        )
        full_itinerary = {}
        activities = self.cursor.fetchall()
        
        # Get column names for dict conversion
        columns = [desc[0] for desc in self.cursor.description]

        for row in activities:
            activity_dict = dict(zip(columns, row))
            day = activity_dict.pop('day')
            if day not in full_itinerary:
                full_itinerary[day] = []
            full_itinerary[day].append(activity_dict)
            
        return full_itinerary

    def __del__(self):
        """
        Destructor to ensure the database connection is closed.
        """
        if self.conn:
            self.conn.close()
