"""
Update ReviewNum in restaurants database based on actual review counts from Reviews.csv
"""
import sqlite3
import pandas as pd
from pathlib import Path
import sys
import io

# Set standard output encoding to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def update_review_counts():
    """Update ReviewNum field in restaurants table based on actual review counts"""

    db_path = './data/restaurants.db'
    reviews_path = './data/Reviews.csv'

    # Check if files exist
    if not Path(db_path).exists():
        print(f"[Error] Database not found: {db_path}")
        print("Please run migrate_to_db.py first")
        return

    if not Path(reviews_path).exists():
        print(f"[Error] Reviews file not found: {reviews_path}")
        return

    print("[Start] Updating review counts...")

    # Read reviews CSV
    print(f"[Reading] Reviews from: {reviews_path}")
    reviews_df = pd.read_csv(reviews_path, encoding='utf-8-sig')

    # Count reviews per restaurant
    review_counts = reviews_df.groupby('Restaurant_ID').size().reset_index(name='ReviewCount')
    print(f"[Info] Found {len(review_counts)} restaurants with reviews")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update ReviewNum for each restaurant
    updated_count = 0
    for _, row in review_counts.iterrows():
        restaurant_id = row['Restaurant_ID']
        review_count = row['ReviewCount']

        cursor.execute('''
            UPDATE restaurants
            SET ReviewNum = ?
            WHERE Restaurant_ID = ?
        ''', (review_count, restaurant_id))
        updated_count += 1

    # Commit changes
    conn.commit()

    print(f"[Success] Updated ReviewNum for {updated_count} restaurants")

    # Verify the update
    print("\n[Verification] Sample of updated restaurants:")
    cursor.execute('''
        SELECT Restaurant_ID, Name, ReviewNum
        FROM restaurants
        WHERE ReviewNum IS NOT NULL
        ORDER BY Restaurant_ID
        LIMIT 10
    ''')

    results = cursor.fetchall()
    for restaurant_id, name, review_num in results:
        print(f"   ID: {restaurant_id} | {name} | Reviews: {review_num}")

    # Show statistics
    cursor.execute('SELECT COUNT(*) FROM restaurants WHERE ReviewNum = 30')
    count_30 = cursor.fetchone()[0]
    print(f"\n[Statistics] Restaurants with exactly 30 reviews: {count_30}")

    cursor.execute('SELECT MIN(ReviewNum), MAX(ReviewNum), AVG(ReviewNum) FROM restaurants WHERE ReviewNum IS NOT NULL')
    min_rev, max_rev, avg_rev = cursor.fetchone()
    print(f"[Statistics] Review count range: {min_rev} - {max_rev}, Average: {avg_rev:.2f}")

    # Close connection
    conn.close()

    print("\n[Complete] Review counts updated successfully!")

if __name__ == '__main__':
    update_review_counts()
