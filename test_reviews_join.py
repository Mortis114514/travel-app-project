import pandas as pd

print("=" * 60)
print("Testing Restaurant and Reviews CSV Relationship")
print("=" * 60)

# 讀取兩個 CSV 檔案
df_restaurants = pd.read_csv('data/Kyoto_Restaurant_Info.csv')
df_reviews = pd.read_csv('data/Reviews.csv')

print(f"\n[1] Basic Information")
print(f"    Restaurants: {len(df_restaurants)} rows")
print(f"    Reviews: {len(df_reviews)} rows")

# 檢查欄位
print(f"\n[2] Column Check")
print(f"    Restaurant columns: {list(df_restaurants.columns[:5])}...")
print(f"    Reviews columns: {list(df_reviews.columns)}")

# 檢查 Restaurant_ID 是否存在
print(f"\n[3] Restaurant_ID Check")
print(f"    'Restaurant_ID' in restaurants: {'Restaurant_ID' in df_restaurants.columns}")
print(f"    'Restaurant_ID' in reviews: {'Restaurant_ID' in df_reviews.columns}")

# 檢查 ID 範圍
print(f"\n[4] ID Range Check")
print(f"    Restaurant IDs range: {df_restaurants['Restaurant_ID'].min()} to {df_restaurants['Restaurant_ID'].max()}")
print(f"    Review Restaurant_IDs range: {df_reviews['Restaurant_ID'].min()} to {df_reviews['Restaurant_ID'].max()}")

# 檢查每個餐廳的評論數
print(f"\n[5] Reviews per Restaurant")
reviews_count = df_reviews.groupby('Restaurant_ID').size()
print(f"    Min reviews per restaurant: {reviews_count.min()}")
print(f"    Max reviews per restaurant: {reviews_count.max()}")
print(f"    Average reviews per restaurant: {reviews_count.mean():.1f}")

# 測試 JOIN 操作
print(f"\n[6] Testing JOIN Operation")
df_joined = pd.merge(df_reviews, df_restaurants, on='Restaurant_ID', how='left')
print(f"    Joined dataframe rows: {len(df_joined)}")
print(f"    Joined dataframe columns: {len(df_joined.columns)}")

# 檢查是否有無法匹配的評論
unmatched = df_joined[df_joined['Name'].isna()]
print(f"    Unmatched reviews: {len(unmatched)}")

# 顯示範例資料
print(f"\n[7] Sample Joined Data (First Restaurant)")
print("=" * 60)
sample = df_joined[df_joined['Restaurant_ID'] == 1][['Review_ID', 'Restaurant_ID', 'Name', 'Review_Text', 'Review_Rating']].head(5)
print(sample.to_string(index=False))

print(f"\n[8] Calculate Average Rating per Restaurant")
avg_ratings = df_reviews.groupby('Restaurant_ID')['Review_Rating'].agg(['mean', 'count']).round(2)
avg_ratings.columns = ['Avg_Review_Rating', 'Review_Count']
df_comparison = pd.merge(df_restaurants[['Restaurant_ID', 'Name', 'TotalRating']], avg_ratings, on='Restaurant_ID', how='left')

print("\nFirst 10 restaurants comparison:")
print(df_comparison.head(10).to_string(index=False))

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
print("\nConclusion:")
if len(unmatched) == 0 and len(df_joined) == len(df_reviews):
    print("[SUCCESS] All reviews successfully matched with restaurants")
    print("[SUCCESS] The two CSV files can be properly joined!")
else:
    print("[ERROR] Some issues found with the join operation")
