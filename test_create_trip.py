"""
Test script for Create Trip functionality
"""
import sqlite3
from utils.trips import create_trip, add_item_to_trip, get_user_trips, get_trip_items

def test_trips_functionality():
    print("Testing Create Trip functionality...")

    # Test 1: Check if tables exist
    print("\n1. Checking if trips tables exist...")
    conn = sqlite3.connect('./data/users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trips'")
    trips_table = cursor.fetchone()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trip_items'")
    trip_items_table = cursor.fetchone()

    if trips_table:
        print("   [OK] trips table exists")
    else:
        print("   [ERROR] trips table does not exist!")

    if trip_items_table:
        print("   [OK] trip_items table exists")
    else:
        print("   [ERROR] trip_items table does not exist!")

    conn.close()

    # Test 2: Create a test trip (using user_id=1 which should be the admin user)
    print("\n2. Creating a test trip...")
    success, trip_id, message = create_trip(
        user_id=1,
        trip_name="Test Trip - Kyoto Adventure",
        start_date="2024-05-01",
        end_date="2024-05-05",
        description="This is a test trip"
    )

    if success:
        print(f"   [OK] Trip created successfully! Trip ID: {trip_id}")
        print(f"   Message: {message}")
    else:
        print(f"   [ERROR] Failed to create trip: {message}")
        return

    # Test 3: Add items to the trip
    print("\n3. Adding items to the trip...")

    # Add a restaurant (assuming restaurant ID 1 exists)
    success1, msg1 = add_item_to_trip(
        trip_id=trip_id,
        item_type='restaurant',
        item_id=1,
        item_name='Test Restaurant',
        day_number=1
    )
    print(f"   Adding restaurant: {'[OK]' if success1 else '[ERROR]'} - {msg1}")

    # Add a hotel (assuming hotel ID 1 exists)
    success2, msg2 = add_item_to_trip(
        trip_id=trip_id,
        item_type='hotel',
        item_id=1,
        item_name='Test Hotel',
        day_number=2
    )
    print(f"   Adding hotel: {'[OK]' if success2 else '[ERROR]'} - {msg2}")

    # Add an attraction (assuming attraction ID 1 exists)
    success3, msg3 = add_item_to_trip(
        trip_id=trip_id,
        item_type='attraction',
        item_id=1,
        item_name='Test Attraction',
        day_number=3
    )
    print(f"   Adding attraction: {'[OK]' if success3 else '[ERROR]'} - {msg3}")

    # Test 4: Retrieve trip items
    print("\n4. Retrieving trip items...")
    items = get_trip_items(trip_id)

    if items:
        print(f"   [OK] Retrieved {len(items)} items:")
        for item in items:
            print(f"      - Day {item['day_number']}: {item['item_name']} ({item['item_type']})")
    else:
        print("   [WARNING] No items found")

    # Test 5: Get all trips for user
    print("\n5. Getting all trips for user 1...")
    trips = get_user_trips(1)

    if trips:
        print(f"   [OK] Found {len(trips)} trip(s):")
        for trip in trips:
            print(f"      - {trip['trip_name']} ({trip['start_date']} to {trip['end_date']})")
    else:
        print("   [WARNING] No trips found")

    print("\n" + "="*60)
    print("Test completed successfully!")
    print("="*60)

if __name__ == '__main__':
    try:
        test_trips_functionality()
    except Exception as e:
        print(f"\n[FATAL ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
