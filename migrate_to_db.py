"""
数据库迁移脚本
将 CSV 数据迁移到 SQLite 数据库
"""
import sqlite3
import pandas as pd
from pathlib import Path
import sys
import io

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def migrate_csv_to_database():
    """将 CSV 数据迁移到 SQLite 数据库"""

    # 数据库路径
    db_path = './data/restaurants.db'

    print("[开始] 数据迁移...")

    # 连接数据库（如果不存在会自动创建）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ===== 创建餐厅表 =====
    print("[创建] 餐厅表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS restaurants (
            Restaurant_ID INTEGER PRIMARY KEY,
            Name TEXT NOT NULL,
            JapaneseName TEXT,
            Station TEXT,
            FirstCategory TEXT,
            SecondCategory TEXT,
            TotalRating REAL,
            Lat REAL,
            Long REAL,
            DinnerPrice TEXT,
            LunchPrice TEXT,
            Price_Category TEXT,
            DinnerRating REAL,
            LunchRating REAL,
            ReviewNum INTEGER,
            Rating_Category TEXT
        )
    ''')

    # 创建索引以加速查询
    print("[索引] 创建索引...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON restaurants(Name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_station ON restaurants(Station)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_first_category ON restaurants(FirstCategory)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_total_rating ON restaurants(TotalRating DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rating_category ON restaurants(Rating_Category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_num ON restaurants(ReviewNum DESC)')

    # ===== 导入餐厅数据 =====
    csv_path = './data/Kyoto_Restaurant_Info_Full.csv'

    if Path(csv_path).exists():
        print(f"[读取] CSV 文件: {csv_path}")
        df = pd.read_csv(csv_path)

        # 清空现有数据
        cursor.execute('DELETE FROM restaurants')

        # 插入数据
        print(f"[插入] {len(df)} 条餐厅记录...")
        df.to_sql('restaurants', conn, if_exists='replace', index=False)

        print(f"[成功] 导入 {len(df)} 条餐厅记录")
    else:
        print(f"[错误] 找不到文件: {csv_path}")

    # ===== 检查 Reviews.csv 是否存在并导入 =====
    reviews_path = './data/Reviews.csv'
    if Path(reviews_path).exists():
        print(f"\n[读取] 评论文件: {reviews_path}")

        # 创建评论表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                Review_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Restaurant_ID INTEGER,
                ReviewText TEXT,
                Rating REAL,
                ReviewDate TEXT,
                FOREIGN KEY (Restaurant_ID) REFERENCES restaurants(Restaurant_ID)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurant_id ON reviews(Restaurant_ID)')

        # 读取并插入评论数据
        reviews_df = pd.read_csv(reviews_path)
        reviews_df.to_sql('reviews', conn, if_exists='replace', index=False)

        print(f"[成功] 导入 {len(reviews_df)} 条评论记录")
    else:
        print(f"[信息] 未找到评论文件: {reviews_path}（可选）")

    # ===== 验证数据 =====
    print("\n[验证] 数据...")
    cursor.execute('SELECT COUNT(*) FROM restaurants')
    count = cursor.fetchone()[0]
    print(f"[成功] 数据库中共有 {count} 条餐厅记录")

    cursor.execute('SELECT Name, TotalRating, Station FROM restaurants ORDER BY TotalRating DESC LIMIT 5')
    top_restaurants = cursor.fetchall()
    print("\n[TOP 5] 评分最高的餐厅:")
    for i, (name, rating, station) in enumerate(top_restaurants, 1):
        print(f"   {i}. {name} - {rating:.2f} ({station})")

    # 提交更改并关闭连接
    conn.commit()
    conn.close()

    print(f"\n[完成] 数据迁移完成！数据库位于: {db_path}")

if __name__ == '__main__':
    migrate_csv_to_database()
