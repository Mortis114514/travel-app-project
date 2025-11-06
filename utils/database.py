"""
数据库工具模块
提供高效的数据库查询功能
"""
import sqlite3
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from contextlib import contextmanager

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
        keyword: 搜索关键词（搜索餐厅名、日文名、类别、车站）
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
        # 构建 SQL 查询
        query_parts = ["SELECT * FROM restaurants WHERE 1=1"]
        params = []

        # 关键词搜索
        if keyword and keyword.strip():
            query_parts.append("""
                AND (
                    Name LIKE ? OR
                    JapaneseName LIKE ? OR
                    FirstCategory LIKE ? OR
                    SecondCategory LIKE ? OR
                    Station LIKE ?
                )
            """)
            keyword_pattern = f"%{keyword.strip()}%"
            params.extend([keyword_pattern] * 5)

        # 料理类型筛选
        if cuisine:
            query_parts.append("AND SecondCategory = ?")
            params.append(cuisine)

        # 评分范围筛选
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

        # 价格范围筛选
        if price_range and isinstance(price_range, (list, tuple)) and len(price_range) == 2:
            try:
                min_price, max_price = float(price_range[0]), float(price_range[1])
                # 使用 SQL 计算平均价格（使用 COALESCE 处理 NULL 值）
                # 如果只有一个价格，使用该价格；如果两个都有，使用平均值
                if max_price < 30000:
                    query_parts.append("""
                        AND (
                            CASE
                                WHEN DinnerPrice IS NOT NULL AND DinnerPrice != ''
                                     AND LunchPrice IS NOT NULL AND LunchPrice != ''
                                THEN (CAST(REPLACE(REPLACE(DinnerPrice, '¥', ''), '~', '') AS REAL) +
                                      CAST(REPLACE(REPLACE(LunchPrice, '¥', ''), '~', '') AS REAL)) / 2.0
                                WHEN DinnerPrice IS NOT NULL AND DinnerPrice != ''
                                THEN CAST(REPLACE(REPLACE(DinnerPrice, '¥', ''), '~', '') AS REAL)
                                WHEN LunchPrice IS NOT NULL AND LunchPrice != ''
                                THEN CAST(REPLACE(REPLACE(LunchPrice, '¥', ''), '~', '') AS REAL)
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
                                THEN (CAST(REPLACE(REPLACE(DinnerPrice, '¥', ''), '~', '') AS REAL) +
                                      CAST(REPLACE(REPLACE(LunchPrice, '¥', ''), '~', '') AS REAL)) / 2.0
                                WHEN DinnerPrice IS NOT NULL AND DinnerPrice != ''
                                THEN CAST(REPLACE(REPLACE(DinnerPrice, '¥', ''), '~', '') AS REAL)
                                WHEN LunchPrice IS NOT NULL AND LunchPrice != ''
                                THEN CAST(REPLACE(REPLACE(LunchPrice, '¥', ''), '~', '') AS REAL)
                                ELSE 0
                            END
                        ) >= ?
                    """)
                    params.append(min_price)
            except (ValueError, TypeError):
                pass

        # 评论数筛选
        if min_reviews:
            try:
                min_reviews_int = int(min_reviews)
                if min_reviews_int > 0:
                    query_parts.append("AND ReviewNum >= ?")
                    params.append(min_reviews_int)
            except (ValueError, TypeError):
                pass

        # 车站筛选
        if stations and len(stations) > 0:
            placeholders = ','.join(['?'] * len(stations))
            query_parts.append(f"AND Station IN ({placeholders})")
            params.extend(stations)

        # 排序
        order_clauses = []
        if sort_by == 'rating_desc':
            order_clauses = ['TotalRating DESC', 'ReviewNum DESC']
        elif sort_by == 'reviews_desc':
            order_clauses = ['ReviewNum DESC', 'TotalRating DESC']
        elif sort_by == 'name_asc':
            order_clauses = ['Name ASC']
        elif sort_by == 'price_asc':
            order_clauses = ['(DinnerPrice + LunchPrice) ASC']
        elif sort_by == 'price_desc':
            order_clauses = ['(DinnerPrice + LunchPrice) DESC']

        if order_clauses:
            query_parts.append(f"ORDER BY {', '.join(order_clauses)}")

        # 执行查询
        query = ' '.join(query_parts)
        df = pd.read_sql_query(query, conn, params=params)

    return df

def get_unique_stations() -> List[str]:
    """
    获取所有唯一的车站名称

    Returns:
        List[str]: 车站名称列表（已排序）
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
    获取所有唯一的料理类型

    Returns:
        List[str]: 料理类型列表（已排序）
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
    获取餐厅总数

    Returns:
        int: 餐厅数量
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM restaurants")
        count = cursor.fetchone()[0]
    return count

def get_top_rated_restaurants(limit: int = 10, min_reviews: int = 10) -> pd.DataFrame:
    """
    获取评分最高的餐厅（需要最少评论数）

    Args:
        limit: 返回数量
        min_reviews: 最少评论数

    Returns:
        DataFrame: 高评分餐厅
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
    根据评分类别获取餐厅

    Args:
        rating_category: 评分类别（例如 "4~5 星餐廳"）

    Returns:
        DataFrame: 该类别的餐厅
    """
    with get_db_connection() as conn:
        query = """
            SELECT * FROM restaurants
            WHERE Rating_Category = ?
            ORDER BY TotalRating DESC
        """
        df = pd.read_sql_query(query, conn, params=(rating_category,))
    return df
