import pandas as pd

print("=" * 60)
print("Review Rating Distribution Analysis")
print("=" * 60)

# 讀取評論資料
df_reviews = pd.read_csv('data/Reviews.csv')

# 計算整體星級分布
print("\n[1] Overall Rating Distribution")
rating_counts = df_reviews['Review_Rating'].value_counts().sort_index()
rating_percentages = (rating_counts / len(df_reviews) * 100).round(2)

for rating in range(1, 6):
    count = rating_counts.get(rating, 0)
    percentage = rating_percentages.get(rating, 0)
    bar = '█' * int(percentage / 2)
    print(f"    {rating} star: {count:>5} reviews ({percentage:>5.2f}%) {bar}")

print(f"\n    Total: {len(df_reviews)} reviews")

# 檢查評論語言多樣性
print("\n[2] Review Language Diversity (Sample 100 random reviews)")
sample_reviews = df_reviews.sample(min(100, len(df_reviews)))

# 簡單的語言檢測
def detect_language(text):
    if any('\u4e00' <= char <= '\u9fff' for char in text):  # 中文字符
        if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):  # 日文假名
            return 'Japanese'
        return 'Chinese'
    return 'English'

lang_counts = sample_reviews['Review_Text'].apply(detect_language).value_counts()
print("    Language distribution in sample:")
for lang, count in lang_counts.items():
    percentage = round((count / len(sample_reviews) * 100), 1)
    print(f"    - {lang}: {count} ({percentage}%)")

# 檢查不同餐廳的星級分布
print("\n[3] Rating Distribution by Restaurant Quality")
df_restaurants = pd.read_csv('data/Kyoto_Restaurant_Info.csv')
df_merged = pd.merge(df_reviews, df_restaurants[['Restaurant_ID', 'TotalRating']], on='Restaurant_ID')

# 按餐廳總評分分組
df_merged['Rating_Group'] = pd.cut(df_merged['TotalRating'],
                                     bins=[0, 3.0, 3.4, 3.7, 5.0],
                                     labels=['Low (< 3.0)', 'Medium (3.0-3.4)', 'Medium-High (3.4-3.7)', 'High (>= 3.7)'])

for group in ['Low (< 3.0)', 'Medium (3.0-3.4)', 'Medium-High (3.4-3.7)', 'High (>= 3.7)']:
    group_data = df_merged[df_merged['Rating_Group'] == group]
    if len(group_data) > 0:
        print(f"\n    {group}:")
        group_rating_dist = group_data['Review_Rating'].value_counts().sort_index()
        for rating in range(1, 6):
            count = group_rating_dist.get(rating, 0)
            percentage = round((count / len(group_data) * 100), 1)
            print(f"      {rating} star: {percentage:>5.1f}%")

# 顯示範例評論（不同語言）
print("\n[4] Sample Reviews (Different Languages)")
print("=" * 60)

# 找一些不同語言的範例
sample_en = df_reviews[df_reviews['Review_Text'].apply(detect_language) == 'English'].head(2)
sample_zh = df_reviews[df_reviews['Review_Text'].apply(detect_language) == 'Chinese'].head(2)
sample_ja = df_reviews[df_reviews['Review_Text'].apply(detect_language) == 'Japanese'].head(2)

print("\nEnglish Reviews:")
for _, row in sample_en.iterrows():
    print(f"  [{row['Review_Rating']} stars] {row['Review_Text'][:80]}")

print("\nChinese Reviews:")
for _, row in sample_zh.iterrows():
    print(f"  [{row['Review_Rating']} stars] {row['Review_Text'][:80]}")

print("\nJapanese Reviews:")
for _, row in sample_ja.iterrows():
    print(f"  [{row['Review_Rating']} stars] {row['Review_Text'][:80]}")

print("\n" + "=" * 60)
print("Analysis Complete!")
print("=" * 60)
