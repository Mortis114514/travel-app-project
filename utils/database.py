"""
数据库工具模块
提供高效的数据库查询功能
"""
import sqlite3
import pandas as pd
import numpy as np
import re
from typing import List, Optional, Tuple, Dict, Any
from contextlib import contextmanager
import math
import random

# 数据库路径
DB_PATH = './data/travel.db'

def initialize_db():
    """
    Initializes the database by creating necessary tables if they don't exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create restaurants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS restaurants (
                Restaurant_ID INTEGER PRIMARY KEY,
                Name TEXT,
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
        """)

        # Create trips table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                trip_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Create activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                day INTEGER NOT NULL,
                start_time TEXT NOT NULL, -- Stored as 'HH:MM'
                end_time TEXT NOT NULL,   -- Stored as 'HH:MM'
                location_name TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips (id)
            )
        """)
        conn.commit()
    print("Database tables (restaurants, trips, activities) initialized successfully or already exist.")

@contextmanager
def get_db_connection():
    """
    数据库连接上下文管理器
    自动处理连接的打开和关闭
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
    try:
        yield conn
    finally:
        conn.close()

def get_all_restaurants(sort_by='TotalRating', ascending=False) -> pd.DataFrame:
    """
    获取所有餐厅数据

    Args:
        sort_by: 排序字段
        ascending: 是否升序

    Returns:
        DataFrame: 餐厅数据
    """
    try:
        with get_db_connection() as conn:
            query = f"""
                SELECT * FROM restaurants
                ORDER BY {sort_by} {'ASC' if ascending else 'DESC'}
            """
            df = pd.read_sql_query(query, conn)
        return df
    except sqlite3.OperationalError as e:
        print(f"Warning: Could not read 'restaurants' table. It might not exist or be empty. Error: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

def get_random_top_restaurants(n=5, min_rating=4.0) -> pd.DataFrame:
    """
    随机获取高评分餐厅

    Args:
        n: 获取数量
        min_rating: 最低评分

    Returns:
        DataFrame: 随机高评分餐厅
    """
    with get_db_connection() as conn:
        query = """
            SELECT * FROM restaurants
            WHERE TotalRating >= ?
            ORDER BY RANDOM()
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(min_rating, n))
    return df

def search_restaurants(
    keyword: Optional[str] = None,
    cuisine: Optional[str] = None,
    rating: Optional[str] = None,
    price_range: Optional[Tuple[float, float]] = None,
    min_reviews: Optional[int] = None,
    stations: Optional[List[str]] = None,
    sort_by: str = 'rating_desc'
) -> pd.DataFrame:
    """
    高级餐厅搜索功能（使用 SQL 查询）

    Args:
        keyword: 搜索关键词（仅搜索餐厅名称和日文名称）
        cuisine: 料理类型（FirstCategory）
        rating: 评分范围（例如 "4-5"）
        price_range: 价格范围 (min, max)
        min_reviews: 最少评论数
        stations: 车站列表
        sort_by: 排序方式

    Returns:
        DataFrame: 筛选后的餐厅数据
    """
    with get_db_connection() as conn:
        # 建構 SQL 查询
        query_parts = ["SELECT * FROM restaurants WHERE 1=1"]
        params = []

        # 關鍵字搜索（僅搜索餐廳名稱）
        if keyword and keyword.strip():
            query_parts.append("""
                AND (
                    Name LIKE ? OR
                    JapaneseName LIKE ?
                )
            """)
            keyword_pattern = f"%{keyword.strip()}%"
            params.extend([keyword_pattern] * 2)

        # 料理類型篩選
        if cuisine:
            query_parts.append("AND SecondCategory = ?")
            params.append(cuisine)

        # 評分篩選
        if rating:
            if isinstance(rating, str) and '-' in rating:
                try:
                    min_rating, max_rating = rating.split('-')
                    min_rating = float(min_rating)
                    max_rating = float(max_rating)
                    if max_rating < 5:
                        query_parts.append("AND TotalRating >= ? AND TotalRating < ?")
                        params.extend([min_rating, max_rating])
                    else:
                        query_parts.append("AND TotalRating >= ? AND TotalRating <= ?")
                        params.extend([min_rating, max_rating])
                except (ValueError, AttributeError):
                    pass
            else:
                try:
                    rating_num = float(rating)
                    query_parts.append("AND TotalRating >= ?")
                    params.append(rating_num)
                except (ValueError, TypeError):
                    pass

        # 價格範圍篩選
        if price_range and isinstance(price_range, (list, tuple)) and len(price_range) == 2:
            try:
                min_price, max_price = float(price_range[0]), float(price_range[1])
                # 使用 SQL 計算average（使用 COALESCE 處理 NULL 值）
                # 如果只有一個價格，使用該價格；如果兩個都有，使用平均值
                if max_price < 30000:
                    query_parts.append("""
                        AND (
                            CASE
                                WHEN DinnerPrice IS NOT NULL AND DinnerPrice != ''
                                     AND LunchPrice IS NOT NULL AND LunchPrice != ''
                                THEN (CAST(SUBSTR(DinnerPrice, 2, INSTR(DinnerPrice, '～') - 2) AS REAL) +
                                      CAST(SUBSTR(LunchPrice, 2, INSTR(LunchPrice, '～') - 2) AS REAL)) / 2.0
                                WHEN DinnerPrice IS NOT NULL AND DinnerPrice != ''
                                THEN CAST(SUBSTR(DinnerPrice, 2, INSTR(DinnerPrice, '～') - 2) AS REAL)
                                WHEN LunchPrice IS NOT NULL AND LunchPrice != ''
                                THEN CAST(SUBSTR(LunchPrice, 2, INSTR(LunchPrice, '～') - 2) AS REAL)
                                ELSE 0
                            END
                        ) BETWEEN ? AND ?
                    """)
                    params.extend([min_price, max_price])
                else:
                    query_parts.append("""
                        AND (
                            CASE
                                WHEN DinnerPrice IS NOT NULL AND DinnerPrice != ''
                                     AND LunchPrice IS NOT NULL AND LunchPrice != ''
                                THEN (CAST(SUBSTR(DinnerPrice, 2, INSTR(DinnerPrice, '～') - 2) AS REAL) +
                                      CAST(SUBSTR(LunchPrice, 2, INSTR(LunchPrice, '～') - 2) AS REAL)) / 2.0
                                WHEN DinnerPrice IS NOT NULL AND DinnerPrice != ''
                                THEN CAST(SUBSTR(DinnerPrice, 2, INSTR(DinnerPrice, '～') - 2) AS REAL)
                                WHEN LunchPrice IS NOT NULL AND LunchPrice != ''
                                THEN CAST(SUBSTR(LunchPrice, 2, INSTR(LunchPrice, '～') - 2) AS REAL)
                                ELSE 0
                            END
                        ) >= ?
                    """)
                    params.append(min_price)
            except (ValueError, TypeError):
                pass

        # 評論數筛选
        if min_reviews:
            try:
                min_reviews_int = int(min_reviews)
                if min_reviews_int > 0:
                    query_parts.append("AND ReviewNum >= ?")
                    params.append(min_reviews_int)
            except (ValueError, TypeError):
                pass

        # 車站筛选
        if stations and len(stations) > 0:
            placeholders = ','.join(['?'] * len(stations))
            query_parts.append(f"AND Station IN ({placeholders})")
            params.extend(stations)

        # 排序
        order_clauses = []
        if keyword and keyword.strip():
            # 優先排序：名稱完全符合 > 名稱開頭 > 日文名稱開頭 > 其他
            order_clauses.append("""
                CASE
                    WHEN Name = ? THEN 1
                    WHEN JapaneseName = ? THEN 2
                    WHEN Name LIKE ? THEN 3
                    WHEN JapaneseName LIKE ? THEN 4
                    WHEN Name LIKE ? THEN 5
                    WHEN JapaneseName LIKE ? THEN 6
                    ELSE 7
                END
            """)
            keyword_param = keyword.strip()
            params.extend([
                keyword_param,
                keyword_param,
                f"{keyword_param}%",
                f"{keyword_param}%",
                f"%{keyword_param}%",
                f"%{keyword_param}%"
            ])

        if sort_by == 'rating_desc':
            order_clauses.extend(['TotalRating DESC', 'ReviewNum DESC'])
        elif sort_by == 'reviews_desc':
            order_clauses.extend(['ReviewNum DESC', 'TotalRating DESC'])
        elif sort_by == 'name_asc':
            order_clauses.append('Name ASC')
        elif sort_by == 'price_asc':
            # 價格排序（使用 SUBSTR 提取最低價格）
            order_clauses.append("CAST(SUBSTR(DinnerPrice, 2, INSTR(DinnerPrice, '～') - 2) AS REAL) ASC")
        elif sort_by == 'price_desc':
            order_clauses.append("CAST(SUBSTR(DinnerPrice, 2, INSTR(DinnerPrice, '～') - 2) AS REAL) DESC")

        if order_clauses:
            query_parts.append(f"ORDER BY {', '.join(order_clauses)}")

        # 執行查询
        query = ' '.join(query_parts)
        df = pd.read_sql_query(query, conn, params=params)

    return df

def get_unique_stations() -> List[str]:
    """
    獲取所有唯一車站的名稱

    Returns:
        List[str]: 車站名稱列表
    """
    with get_db_connection() as conn:
        query = """
            SELECT DISTINCT Station
            FROM restaurants
            WHERE Station IS NOT NULL
            ORDER BY Station
        """
        cursor = conn.cursor()
        cursor.execute(query)
        stations = [row[0] for row in cursor.fetchall()]
    return stations

def get_unique_cuisines() -> List[str]:
    """
    獲取料理類型

    Returns:
        List[str]: 料理類型表（已排序）
    """
    with get_db_connection() as conn:
        query = """
            SELECT DISTINCT SecondCategory
            FROM restaurants
            WHERE SecondCategory IS NOT NULL
            ORDER BY SecondCategory
        """
        cursor = conn.cursor()
        cursor.execute(query)
        cuisines = [row[0] for row in cursor.fetchall()]
    return cuisines

def get_restaurant_by_id(restaurant_id: int) -> Optional[Dict[str, Any]]:
    """
    根据 ID 获取餐厅详情

    Args:
        restaurant_id: 餐厅 ID

    Returns:
        Dict: 餐厅信息，如果不存在返回 None
    """
    with get_db_connection() as conn:
        query = "SELECT * FROM restaurants WHERE Restaurant_ID = ?"
        cursor = conn.cursor()
        cursor.execute(query, (restaurant_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None

def get_restaurant_count() -> int:
    """
    獲取餐厅总数

    Returns:
        int: 餐廳数量
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM restaurants")
        count = cursor.fetchone()[0]
    return count

def get_top_rated_restaurants(limit: int = 10, min_reviews: int = 10) -> pd.DataFrame:
    """
    獲取評分最高的餐廳（需要最少評論数）

    Args:
        limit: 返回数量
        min_reviews: 最少評論数

    Returns:
        DataFrame: 高評分餐廳
    """
    with get_db_connection() as conn:
        query = """
            SELECT * FROM restaurants
            WHERE ReviewNum >= ?
            ORDER BY TotalRating DESC, ReviewNum DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(min_reviews, limit))
    return df

def get_restaurants_by_category(rating_category: str) -> pd.DataFrame:
    """
    根据評分類別獲取餐廳

    Args:
        rating_category: 評分類別（例如 "4~5 星餐廳"）

    Returns:
        DataFrame: 該類別的餐廳
    """
    with get_db_connection() as conn:
        query = """
            SELECT * FROM restaurants
            WHERE Rating_Category = ?
            ORDER BY TotalRating DESC
        """
        df = pd.read_sql_query(query, conn, params=(rating_category,))
    return df

def get_nearby_restaurants(lat: float, long: float, limit: int = 5, exclude_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    獲取附近的餐廳（使用 Haversine 距離計算）

    Args:
        lat: 中心緯度
        long: 中心經度
        limit: 返回數量
        exclude_id: 排除的餐廳 ID（通常是當前餐廳）

    Returns:
        List[Dict]: 附近餐廳列表，包含距離訊息
    """
    import math

    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        使用 Haversine 公式計算两點之间的距離（公里）
        """
        # 地球半径（公里）
        R = 6371

        # 轉換為弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # 計算差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine 公式
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    with get_db_connection() as conn:
        # 獲取所有有坐標的餐廳
        query = """
            SELECT * FROM restaurants
            WHERE Lat IS NOT NULL AND Long IS NOT NULL
        """

        params = []

        # 如果需要排除當前餐廳
        if exclude_id is not None:
            query += " AND Restaurant_ID != ?"
            params.append(exclude_id)

        cursor = conn.cursor()
        cursor.execute(query, params)

        # 獲取列名
        columns = [description[0] for description in cursor.description]

        # 計算所有餐廳的距離
        restaurants_with_distance = []
        for row in cursor.fetchall():
            restaurant = dict(zip(columns, row))
            # 計算距離
            distance = haversine_distance(lat, long, restaurant['Lat'], restaurant['Long'])
            restaurant['distance'] = distance
            restaurants_with_distance.append(restaurant)

        # 按距離排序並取前 N 個
        restaurants_with_distance.sort(key=lambda x: x['distance'])
        results = restaurants_with_distance[:limit]

    return results

def get_all_hotels():
    """從資料庫獲取所有旅館資料"""
    try:
        hotels_df = pd.read_csv('data/Hotels.csv')
        hotel_types_df = pd.read_csv('data/HotelTypes.csv')
        types_df = pd.read_csv('data/Types.csv')
        
        # 合併旅館類型資訊
        hotels_with_types = hotels_df.merge(
            hotel_types_df, 
            on='Hotel_ID', 
            how='left'
        ).merge(
            types_df, 
            on='Type_ID', 
            how='left'
        )
        
        # 將同一旅館的多個類型合併為列表
        hotels_aggregated = hotels_with_types.groupby('Hotel_ID').agg({
            'HotelName': 'first',
            'Address': 'first',
            'Rating': 'first',
            'UserRatingsTotal': 'first',
            'Lat': 'first',
            'Long': 'first',
            'Place_ID': 'first',
            'TypeName': lambda x: list(x.dropna().unique()) if x.notna().any() else []
        }).reset_index()
        
        # 重命名欄位以保持一致性
        hotels_aggregated.rename(columns={'TypeName': 'Types'}, inplace=True)
        
        return hotels_aggregated
    except Exception as e:
        print(f"Error loading hotels: {e}")
        return pd.DataFrame()

def get_hotel_by_id(hotel_id: int) -> Optional[dict]:
    """根據 ID 獲取單一旅館資料"""
    try:
        hotels_df = get_all_hotels()
        hotel = hotels_df[hotels_df['Hotel_ID'] == hotel_id]
        
        if hotel.empty:
            return None
        
        return hotel.iloc[0].to_dict()
    except Exception as e:
        print(f"Error getting hotel by ID: {e}")
        return None

def get_random_top_hotels(n: int = 5, min_rating: float = 4.0) -> pd.DataFrame:
    """隨機選擇高評分旅館"""
    try:
        hotels_df = get_all_hotels()
        
        # 篩選高評分旅館
        top_hotels = hotels_df[hotels_df['Rating'] >= min_rating]
        
        # 隨機選擇
        if len(top_hotels) > n:
            return top_hotels.sample(n=n, random_state=None)
        else:
            return top_hotels
    except Exception as e:
        print(f"Error getting random top hotels: {e}")
        return pd.DataFrame()

def search_hotels(
    keyword: Optional[str] = None,
    hotel_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    sort_by: str = 'rating_desc'
) -> pd.DataFrame:
    """搜尋旅館 (支援多種篩選條件)"""
    try:
        hotels_df = get_all_hotels()
        
        # 關鍵字搜尋 (名稱或地址)
        if keyword:
            keyword_lower = keyword.lower()
            mask = (
                hotels_df['HotelName'].str.lower().str.contains(keyword_lower, na=False) |
                hotels_df['Address'].str.lower().str.contains(keyword_lower, na=False)
            )
            hotels_df = hotels_df[mask]
        
        # 類型篩選
        if hotel_type:
            hotels_df = hotels_df[
                hotels_df['Types'].apply(lambda types: hotel_type in types if isinstance(types, list) else False)
            ]
        
        # 評分篩選
        if min_rating:
            hotels_df = hotels_df[hotels_df['Rating'] >= min_rating]
        
        # 排序
        if sort_by == 'rating_desc':
            hotels_df = hotels_df.sort_values('Rating', ascending=False)
        elif sort_by == 'rating_asc':
            hotels_df = hotels_df.sort_values('Rating', ascending=True)
        elif sort_by == 'reviews_desc':
            hotels_df = hotels_df.sort_values('UserRatingsTotal', ascending=False)
        elif sort_by == 'name_asc':
            hotels_df = hotels_df.sort_values('HotelName', ascending=True)
        
        return hotels_df
    except Exception as e:
        print(f"Error searching hotels: {e}")
        return pd.DataFrame()

def get_unique_hotel_types() -> List[str]:
    """獲取所有唯一的旅館類型"""
    try:
        types_df = pd.read_csv('data/Types.csv')
        return sorted(types_df['TypeName'].unique().tolist())
    except Exception as e:
        print(f"Error getting hotel types: {e}")
        return []

def get_nearby_hotels(lat: float, lon: float, limit: int = 5, exclude_id: Optional[int] = None) -> List[dict]:
    """獲取附近的旅館 (基於經緯度計算距離)"""
    try:
        hotels_df = get_all_hotels()
        
        # 排除指定的旅館
        if exclude_id:
            hotels_df = hotels_df[hotels_df['Hotel_ID'] != exclude_id]
        
        # 計算距離 (使用 Haversine 公式)
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # 地球半徑 (公里)
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (math.sin(dlat / 2) ** 2 + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c
        
        hotels_df['distance'] = hotels_df.apply(
            lambda row: haversine_distance(lat, lon, row['Lat'], row['Long']),
            axis=1
        )
        
        # 排序並限制數量
        nearby = hotels_df.nsmallest(limit, 'distance')
        
        return nearby.to_dict('records')
    except Exception as e:
        print(f"Error getting nearby hotels: {e}")
        return []

def get_hotels_by_type(type_name: str) -> pd.DataFrame:
    """根據類型獲取旅館列表"""
    try:
        hotels_df = get_all_hotels()
        filtered = hotels_df[
            hotels_df['Types'].apply(lambda types: type_name in types if isinstance(types, list) else False)
        ]
        return filtered.sort_values('Rating', ascending=False)
    except Exception as e:
        print(f"Error getting hotels by type: {e}")
        return pd.DataFrame()
def get_all_reviews() -> pd.DataFrame:
    """讀取你上傳的 Review CSV"""
    try:
        # 注意：這裡讀取的是你提供的 reviews 檔案
        df = pd.read_csv('booking reviews copy.csv')
        # 簡單的清理
        df['reviewed_at'] = pd.to_datetime(df['reviewed_at'], errors='coerce')
        return df
    except FileNotFoundError:
        print("Error: 'booking reviews copy.csv' not found.")
        return pd.DataFrame()

def get_booking_data(hotel_id=None) -> pd.DataFrame:
    """
    讀取由 generate_booking.py 產生的 bookings.csv
    """
    try:
        # 讀取 CSV
        df = pd.read_csv('data/bookings.csv', parse_dates=['booking_date', 'check_in_date'])
        
        # 如果有指定 hotel_id，就只篩選該飯店的資料
        if hotel_id is not None:
            # 確保 ID 格式一致 (轉成 int 比較保險)
            try:
                hotel_id = int(hotel_id)
                df = df[df['hotel_id'] == hotel_id]
            except:
                pass # 如果轉型失敗就不篩選，避免報錯
                
        return df
    except FileNotFoundError:
        print("Error: 'data/bookings.csv' not found. Please run generate_booking.py first.")
        return pd.DataFrame()

def get_revenue_trend(hotel_id=None):
    """取得營收趨勢 (從 CSV 讀取)"""
    df = get_booking_data(hotel_id)
    
    if df.empty:
        return pd.DataFrame()
        
    # 過濾掉取消的訂單
    df = df[df['status'] == 'Confirmed']
    
    # 按月統計
    df['Month'] = df['check_in_date'].dt.to_period('M').astype(str)
    trend = df.groupby('Month')['price_paid'].sum().reset_index()
    trend.rename(columns={'price_paid': 'Revenue'}, inplace=True)
    
    return trend

def get_occupancy_status(hotel_id=None):
    """取得入住狀態分佈 (從 CSV 讀取)"""
    df = get_booking_data(hotel_id)
    
    if df.empty:
        return pd.DataFrame()
        
    # 按月統計
    df['Month'] = df['check_in_date'].dt.to_period('M').astype(str)
    status_counts = df.groupby(['Month', 'status']).size().reset_index(name='Count')
    
    return status_counts

def get_market_analysis_data():
    """
    整合 Bookings, Reviews, Hotels 三方資料
    並自動為沒有評論的旅館生成模擬評分，以確保圖表豐富度
    """
    try:
        # 1. 讀取基礎旅館資料
        hotels = pd.read_csv('data/Hotels.csv')
        hotels = hotels[['Hotel_ID', 'HotelName']]
    except:
        return pd.DataFrame()

    # 2. 處理訂單數據 (計算平均價格 & 取消率)
    try:
        bookings = pd.read_csv('data/bookings.csv')
        booking_stats = bookings.groupby('hotel_id').agg({
            'price_paid': 'mean',
            'status': lambda x: (x == 'Cancelled').sum() / len(x) if len(x) > 0 else 0
        }).reset_index()
        booking_stats.rename(columns={'price_paid': 'avg_price', 'status': 'cancellation_rate'}, inplace=True)
    except:
        return pd.DataFrame()

    # 3. 處理評論數據 (真實數據)
    try:
        reviews = pd.read_csv('data/booking reviews copy.csv')
        review_stats = reviews.groupby('hotel_name').agg({
            'rating': 'mean',
            'review_text': 'count'
        }).reset_index()
        review_stats.rename(columns={'rating': 'avg_rating', 'review_text': 'review_count', 'hotel_name': 'HotelName'}, inplace=True)
        
        # 負評關鍵字分析
        def count_keywords(text_series, keyword):
            if text_series.empty: return 0
            return text_series.str.contains(keyword, case=False, na=False).sum()

        keyword_stats = reviews.groupby('hotel_name')['review_text'].apply(
            lambda x: pd.Series({
                'dirty_mentions': count_keywords(x, 'dirty'),
                'total_reviews': len(x)
            })
        ).unstack().reset_index()
        keyword_stats.rename(columns={'hotel_name': 'HotelName'}, inplace=True)
        
    except:
        review_stats = pd.DataFrame(columns=['HotelName', 'avg_rating', 'review_count'])
        keyword_stats = pd.DataFrame(columns=['HotelName', 'dirty_mentions', 'total_reviews'])

    # 4. 合併資料
    merged_df = pd.merge(hotels, booking_stats, on='Hotel_ID', how='inner')
    final_df = pd.merge(merged_df, review_stats, on='HotelName', how='left')
    final_df = pd.merge(final_df, keyword_stats, on='HotelName', how='left')
    
    # --- 關鍵修改：模擬缺失的評分數據 ---
    # 如果某家飯店有訂單但沒評論，我們隨機給它一個分數，讓圖表好看
    import numpy as np
    
    # 填補評分 (平均 8.0，標準差 1.2)
    missing_mask = final_df['avg_rating'].isna()
    simulated_ratings = np.random.normal(8.0, 1.2, size=missing_mask.sum())
    simulated_ratings = np.clip(simulated_ratings, 2.0, 10.0) # 限制在 2~10 分
    final_df.loc[missing_mask, 'avg_rating'] = simulated_ratings
    
    # 填補評論數 (隨機 5~100 則)
    final_df.loc[final_df['review_count'].isna(), 'review_count'] = np.random.randint(5, 100, size=missing_mask.sum())
    
    # 填補髒亂提及率 (隨機 0% ~ 20%)
    final_df['dirty_mentions'] = final_df['dirty_mentions'].fillna(0)
    final_df['total_reviews'] = final_df['total_reviews'].fillna(final_df['review_count'])
    
    # 對於模擬數據，隨機生成一些 "Dirty" 負評比例
    sim_dirty_mask = (final_df['dirty_mentions'] == 0) & (final_df['review_count'] > 0)
    final_df.loc[sim_dirty_mask, 'dirty_mentions'] = (final_df.loc[sim_dirty_mask, 'review_count'] * np.random.uniform(0, 0.2, size=sim_dirty_mask.sum())).astype(int)

    final_df['avg_price'] = final_df['avg_price'].round(0)
    
    return final_df

def get_all_attractions():
    """從 CSV 獲取所有景點資料"""
    try:
        attractions_df = pd.read_csv('data/Kyoto_attractions.csv')
        
        # 確保 Lat/Lng 為數值
        attractions_df['Lat'] = pd.to_numeric(attractions_df['Lat'], errors='coerce')
        attractions_df['Lng'] = pd.to_numeric(attractions_df['Lng'], errors='coerce')
        
        # 為了保持一致性，將 Lng 重命名為 Long (如果需要)
        # 但 create_hotel_map_chart 用的是 Long, create_restaurant_map_chart 用的是 Long
        attractions_df.rename(columns={'Lng': 'Long'}, inplace=True)
        
        return attractions_df
    except Exception as e:
        print(f"Error loading attractions: {e}")
        return pd.DataFrame()

# ==========================================
#   Attractions Functions (景點專用)
# ==========================================

def get_random_top_attractions(n=5, min_rating=4.0) -> pd.DataFrame:
    """隨機獲取高評分景點 (用於首頁推薦)"""
    with get_db_connection() as conn:
        query = """
            SELECT * FROM attractions 
            WHERE Rating >= ? 
            ORDER BY RANDOM() LIMIT ?
        """
        return pd.read_sql_query(query, conn, params=(min_rating, n))

def get_unique_attraction_types() -> list:
    """獲取所有景點類型 (用於篩選下拉選單)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Type FROM attractions WHERE Type IS NOT NULL ORDER BY Type")
        return [row[0] for row in cursor.fetchall()]

def search_attractions(keyword=None, attr_type=None, min_rating=None, max_rating=None, min_reviews=None, sort_by='rating_desc') -> pd.DataFrame:
    """搜尋景點 (支援關鍵字、類型、評分範圍、最小評論數)"""
    with get_db_connection() as conn:
        query = "SELECT * FROM attractions WHERE 1=1"
        params = []

        if keyword:
            query += " AND (Name LIKE ? OR Address LIKE ?)"
            wildcard = f"%{keyword}%"
            params.extend([wildcard, wildcard])

        if attr_type:
            query += " AND Type = ?"
            params.append(attr_type)

        if min_rating:
            query += " AND Rating >= ?"
            params.append(min_rating)

        if max_rating:
            query += " AND Rating <= ?"
            params.append(max_rating)

        if min_reviews:
            query += " AND UserRatingsTotal >= ?"
            params.append(min_reviews)

        # 排序邏輯
        if sort_by == 'rating_desc':
            query += " ORDER BY Rating DESC, UserRatingsTotal DESC"
        elif sort_by == 'reviews_desc':
            query += " ORDER BY UserRatingsTotal DESC"
        elif sort_by == 'name_asc':
            query += " ORDER BY Name ASC"

        return pd.read_sql_query(query, conn, params=params)

def get_attraction_by_id(attraction_id: int):
    """根據 ID 獲取單一景點詳細資料"""
    print(f"DEBUG: Querying DB for ID {attraction_id} in {DB_PATH}") # 加這行
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 這裡的 "ID" 必須跟你的資料庫欄位名稱完全一樣 (你的資料庫是 ID 大寫)
        cursor.execute("SELECT * FROM attractions WHERE ID = ?", (attraction_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None

def get_combined_analytics_data():
    """
    整合 餐廳、旅館、景點 數據供分析使用 (修復版：含價格模擬與防呆)
    """
    try:
        # 1. 獲取原始資料
        df_rest = get_all_restaurants()
        df_hotel = get_all_hotels()
        df_attr = search_attractions() 

        combined_list = []

        # --- Helper: 餐廳價格解析 ---
        def parse_rest_price(price_str):
            if pd.isna(price_str) or str(price_str).strip() == '': return None
            try:
                # 這裡需要 import re
                nums = re.findall(r'\d+', str(price_str).replace(',', ''))
                if not nums: return None
                prices = [float(n) for n in nums]
                return sum(prices) / len(prices)
            except: return None

        # --- 處理餐廳 ---
        if not df_rest.empty:
            for _, row in df_rest.iterrows():
                try:
                    price = parse_rest_price(row.get('LunchPrice')) or parse_rest_price(row.get('DinnerPrice'))
                    combined_list.append({
                        'ID': row['Restaurant_ID'],
                        'Name': row['Name'],
                        'Lat': row['Lat'],
                        'Long': row['Long'],
                        'Rating': float(row['TotalRating']) if row.get('TotalRating') else 0,
                        'Price': price if price else 0, # 沒價格補 0
                        'Type': 'Restaurant',
                        'SubCategory': row.get('FirstCategory', 'Food')
                    })
                except Exception as e:
                    # 略過錯誤的資料行
                    continue

        # --- 處理旅館 (含價格模擬) ---
        if not df_hotel.empty:
            for _, row in df_hotel.iterrows():
                try:
                    # 1. 取得評分 (若無則預設 3.5)
                    rating = float(row['Rating']) if row.get('Rating') and pd.notna(row['Rating']) else 3.5
                    
                    # 2. 智慧模擬價格邏輯 (解決一直線問題)
                    # 邏輯：基礎房價 3000 + (評分 * 3000)
                    base_price = 3000 + (rating * 3000)
                    
                    # 3. 加入隨機波動 (-20% ~ +50%)
                    random_factor = random.uniform(0.8, 1.5)
                    final_price = int(base_price * random_factor)

                    combined_list.append({
                        'ID': row['Hotel_ID'],
                        'Name': row['HotelName'],
                        'Lat': row['Lat'],
                        'Long': row['Long'],
                        'Rating': rating,
                        'Price': final_price, # 模擬後的價格
                        'Type': 'Hotel',
                        'SubCategory': 'Accommodation'
                    })
                except Exception:
                    continue

        # --- 處理景點 ---
        if not df_attr.empty:
            for _, row in df_attr.iterrows():
                try:
                    # 嘗試兼容 Long 或 Lng 欄位名稱
                    lng = row.get('Long') if 'Long' in row else row.get('Lng')
                    
                    combined_list.append({
                        'ID': row['ID'],
                        'Name': row['Name'],
                        'Lat': row['Lat'],
                        'Long': lng, 
                        'Rating': float(row['Rating']) if row.get('Rating') else 0,
                        'Price': 0, # 景點價格設為 0，不參與矩陣顯示
                        'Type': 'Attraction',
                        'SubCategory': row.get('Type', 'Spot')
                    })
                except Exception:
                    continue

        return pd.DataFrame(combined_list)

    except Exception as e:
        print(f"CRITICAL ERROR in get_combined_analytics_data: {e}")
        # 回傳空 DataFrame 防止整個 App 崩潰
        return pd.DataFrame(columns=['ID', 'Name', 'Lat', 'Long', 'Rating', 'Price', 'Type', 'SubCategory'])