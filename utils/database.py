"""
数据库工具模块
提供高效的数据库查询功能
"""
import sqlite3
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from contextlib import contextmanager
import math

# 数据库路径
DB_PATH = './data/restaurants.db'

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
    with get_db_connection() as conn:
        query = f"""
            SELECT * FROM restaurants
            ORDER BY {sort_by} {'ASC' if ascending else 'DESC'}
        """
        df = pd.read_sql_query(query, conn)
    return df

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