"""
性能对比测试
对比 CSV+pandas 与 SQLite 数据库的性能
"""
import time
import pandas as pd
from utils.database import search_restaurants as db_search

print("=" * 70)
print("性能对比测试: CSV+pandas vs SQLite")
print("=" * 70)

# === 测试 1: 数据加载时间 ===
print("\n[测试 1] 数据加载时间")

# CSV 加载
start = time.time()
csv_df = pd.read_csv('./data/Kyoto_Restaurant_Info_Full.csv')
csv_load_time = (time.time() - start) * 1000
print(f"  CSV 加载: {csv_load_time:.1f}ms ({len(csv_df)} 条记录)")

# 数据库查询（首次）
start = time.time()
db_df = db_search()
db_load_time = (time.time() - start) * 1000
print(f"  数据库查询: {db_load_time:.1f}ms ({len(db_df)} 条记录)")
print(f"  --> 数据库比 CSV 快 {csv_load_time/db_load_time:.1f}x")

# === 测试 2: 关键词搜索 ===
print("\n[测试 2] 关键词搜索 ('kyoto')")

# pandas 搜索
start = time.time()
keyword = 'kyoto'
pandas_result = csv_df[
    csv_df['Name'].str.lower().str.contains(keyword, na=False, regex=False) |
    csv_df['Station'].str.lower().str.contains(keyword, na=False, regex=False)
]
pandas_search_time = (time.time() - start) * 1000
print(f"  pandas: {pandas_search_time:.1f}ms ({len(pandas_result)} 条结果)")

# 数据库搜索
start = time.time()
db_result = db_search(keyword=keyword)
db_search_time = (time.time() - start) * 1000
print(f"  数据库: {db_search_time:.1f}ms ({len(db_result)} 条结果)")
print(f"  --> 数据库比 pandas 快 {pandas_search_time/db_search_time:.1f}x")

# === 测试 3: 评分筛选 ===
print("\n[测试 3] 评分筛选 (4-5 星)")

# pandas 筛选
start = time.time()
pandas_filtered = csv_df[
    (csv_df['TotalRating'] >= 4.0) & (csv_df['TotalRating'] <= 5.0)
].sort_values(by=['TotalRating', 'ReviewNum'], ascending=[False, False])
pandas_filter_time = (time.time() - start) * 1000
print(f"  pandas: {pandas_filter_time:.1f}ms ({len(pandas_filtered)} 条结果)")

# 数据库筛选
start = time.time()
db_filtered = db_search(rating='4-5', sort_by='rating_desc')
db_filter_time = (time.time() - start) * 1000
print(f"  数据库: {db_filter_time:.1f}ms ({len(db_filtered)} 条结果)")
print(f"  --> 数据库比 pandas 快 {pandas_filter_time/db_filter_time:.1f}x")

# === 测试 4: 综合筛选 ===
print("\n[测试 4] 综合筛选 (关键词 + 评分 + 最少评论数)")

# pandas 综合筛选
start = time.time()
keyword = 'sushi'
pandas_complex = csv_df[
    (csv_df['Name'].str.lower().str.contains(keyword, na=False, regex=False) |
     csv_df['FirstCategory'].str.lower().str.contains(keyword, na=False, regex=False)) &
    (csv_df['TotalRating'] >= 4.0) &
    (csv_df['ReviewNum'] >= 10)
].sort_values(by=['TotalRating', 'ReviewNum'], ascending=[False, False])
pandas_complex_time = (time.time() - start) * 1000
print(f"  pandas: {pandas_complex_time:.1f}ms ({len(pandas_complex)} 条结果)")

# 数据库综合筛选
start = time.time()
db_complex = db_search(keyword=keyword, rating='4-5', min_reviews=10, sort_by='rating_desc')
db_complex_time = (time.time() - start) * 1000
print(f"  数据库: {db_complex_time:.1f}ms ({len(db_complex)} 条结果)")
print(f"  --> 数据库比 pandas 快 {pandas_complex_time/db_complex_time:.1f}x")

# === 测试 5: 多次查询（模拟实际使用）===
print("\n[测试 5] 连续 10 次搜索（模拟实际使用场景）")

# pandas 连续搜索
start = time.time()
for _ in range(10):
    _ = csv_df[csv_df['TotalRating'] >= 4.0]
pandas_multi_time = (time.time() - start) * 1000
print(f"  pandas 10 次搜索: {pandas_multi_time:.1f}ms (平均 {pandas_multi_time/10:.1f}ms)")

# 数据库连续搜索
start = time.time()
for _ in range(10):
    _ = db_search(rating='4-5')
db_multi_time = (time.time() - start) * 1000
print(f"  数据库 10 次搜索: {db_multi_time:.1f}ms (平均 {db_multi_time/10:.1f}ms)")
print(f"  --> 数据库比 pandas 快 {pandas_multi_time/db_multi_time:.1f}x")

# === 总结 ===
print("\n" + "=" * 70)
print("性能总结")
print("=" * 70)
print("数据库方案的优势:")
print("  1. 加载速度: 无需每次读取 CSV 文件")
print("  2. 查询速度: 使用索引优化的 SQL 查询")
print("  3. 内存占用: 按需查询，不需要一次性加载全部数据")
print("  4. 可扩展性: 随着数据量增长，性能优势更明显")
print("\n建议: 使用 SQLite 数据库替代 CSV 文件")
print("=" * 70)
