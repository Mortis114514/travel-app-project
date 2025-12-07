"""
Set all restaurants to have exactly 30 reviews in the database
"""
import sqlite3
import pandas as pd

def fix_review_counts():
    """Set ReviewNum to 30 for all restaurants that have reviews"""

    db_path = './data/restaurants.db'
    reviews_path = './data/Reviews.csv'

    print("[Start] Fixing review counts to 30...")

    # Read reviews to get list of restaurant IDs that have reviews
    reviews_df = pd.read_csv(reviews_path, encoding='utf-8-sig')
    restaurant_ids = reviews_df['Restaurant_ID'].unique()

    print(f"[Info] Found {len(restaurant_ids)} restaurants with reviews in CSV")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Set ReviewNum to 30 for all restaurants in the reviews file
    updated_count = 0
    for restaurant_id in restaurant_ids:
        cursor.execute('''
            UPDATE restaurants
            SET ReviewNum = 30
            WHERE Restaurant_ID = ?
        ''', (int(restaurant_id),))
        updated_count += 1

    # Commit changes
    conn.commit()

    print(f"[Success] Updated ReviewNum to 30 for {updated_count} restaurants")

    # Verify the update
    print("\n[Verification] Checking database:")
    cursor.execute('SELECT COUNT(*) FROM restaurants WHERE ReviewNum = 30')
    count_30 = cursor.fetchone()[0]
    print(f"   Restaurants with ReviewNum = 30: {count_30}")

    cursor.execute('SELECT Restaurant_ID, Name, ReviewNum FROM restaurants WHERE ReviewNum = 30 LIMIT 10')
    results = cursor.fetchall()
    print("\n[Sample] First 10 restaurants:")
    for restaurant_id, name, review_num in results:
        print(f"   ID: {restaurant_id} | {name} | Reviews: {review_num}")

    # Close connection
    conn.close()

    print("\n[Complete] All review counts fixed to 30!")

if __name__ == '__main__':
    fix_review_counts()
