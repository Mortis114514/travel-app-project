import sqlite3
import pandas as pd
import os
import numpy as np
import math
import re
import random
from typing import List, Optional, Tuple, Dict, Any
from contextlib import contextmanager

# ==========================================
# 🔥 全域路徑設定 (核心修復)
# ==========================================
# 確保無論從哪裡執行，都指向同一個 travel.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # utils 資料夾
PROJECT_ROOT = os.path.dirname(BASE_DIR) # 專案根目錄
DATA_DIR = os.path.join(PROJECT_ROOT, 'data') # CSV 資料夾
DB_PATH = os.path.join(PROJECT_ROOT, 'travel.db') # 資料庫檔案

print(f"🔗 Database Path set to: {DB_PATH}")
print(f"📂 Data Directory set to: {DATA_DIR}")

# ==========================================
#  資料庫初始化與連線工具
# ==========================================

@contextmanager
def get_db_connection():
    """資料庫連線上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# utils/database.py

def initialize_database():
    """初始化資料庫：合併 CSV 並重建資料表 (含合併 Rating.csv 與 Category.csv)"""
    print("🚀 Starting Database Initialization...")
    
    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Data directory not found at {DATA_DIR}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- 1. 建立功能性表格 ---
    c.execute('''CREATE TABLE IF NOT EXISTS Favorites (
                    user_id TEXT, item_id TEXT, item_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, item_id, item_type))''')

    c.execute('''CREATE TABLE IF NOT EXISTS Trips (
                    trip_id TEXT PRIMARY KEY, user_id TEXT, trip_name TEXT,
                    start_date TEXT, end_date TEXT, trip_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                user_id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL, email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, profile_photo BLOB)''')
    
    print("✔ Functional tables checked.")

    # --- 2. 餐廳資料匯入 (需要合併多個 CSV) ---
    print("⏳ Processing Restaurants...")
    try:
        # 1. 讀取主檔 (Restaurant.csv)
        rest_path = os.path.join(DATA_DIR, 'Restaurant.csv')
        if not os.path.exists(rest_path): rest_path = os.path.join(DATA_DIR, 'restaurant.csv')
        
        df_rest = pd.read_csv(rest_path, encoding='utf-8-sig')
        df_rest.columns = df_rest.columns.str.strip() # 清洗欄位空白
        
        # 2. 合併評分檔 (Rating.csv)
        rating_path = os.path.join(DATA_DIR, 'Rating.csv')
        if os.path.exists(rating_path):
            print("   🔗 Found Rating.csv, merging...")
            df_rating = pd.read_csv(rating_path, encoding='utf-8-sig')
            df_rating.columns = df_rating.columns.str.strip()
            
            # 確保欄位名稱正確
            if 'Rating' in df_rating.columns: 
                df_rating.rename(columns={'Rating': 'TotalRating'}, inplace=True)
            
            # 執行合併 (假設 Key 是 Restaurant_ID)
            if 'Restaurant_ID' in df_rest.columns and 'Restaurant_ID' in df_rating.columns:
                df_rest = pd.merge(df_rest, df_rating[['Restaurant_ID', 'TotalRating']], on='Restaurant_ID', how='left')
        
        # 3. 合併分類檔 (RestaurantCategory.csv + Category.csv)
        # 你的資料夾有 RestaurantCategory.csv (可能是 ID 對照表) 和 Category.csv (分類名稱)
        # 這裡簡化處理：嘗試從 RestaurantCategory.csv 撈資料
        cat_path = os.path.join(DATA_DIR, 'RestaurantCategory.csv')
        if os.path.exists(cat_path):
            print("   🔗 Found RestaurantCategory.csv, merging...")
            df_cat = pd.read_csv(cat_path, encoding='utf-8-sig')
            df_cat.columns = df_cat.columns.str.strip()
            
            # 假設這張表有 Restaurant_ID 和 Category 相關欄位
            # 我們需要先確認一下欄位，這裡做個防呆合併
            if 'Restaurant_ID' in df_cat.columns:
                # 這裡假設分類欄位叫 'Category_ID' 或直接是 'CategoryName'
                # 為了保險，我們把除了 ID 以外的第一個欄位當作分類
                cols_to_merge = [c for c in df_cat.columns if c != 'Restaurant_ID']
                if cols_to_merge:
                    # 如果有 Category.csv，可能還需要再 join 一次，這裡先簡單處理
                    df_rest = pd.merge(df_rest, df_cat[['Restaurant_ID'] + cols_to_merge], on='Restaurant_ID', how='left')
                    
                    # 重新命名找到的分類欄位
                    for col in df_rest.columns:
                        if 'Category' in col and col != 'FirstCategory':
                            df_rest.rename(columns={col: 'FirstCategory'}, inplace=True)
                            break
                            
        # 4. 最終防呆檢查
        if 'TotalRating' not in df_rest.columns: df_rest['TotalRating'] = 0
        if 'FirstCategory' not in df_rest.columns: df_rest['FirstCategory'] = 'Food'
        
        # 存入資料庫
        df_rest.to_sql('restaurants', conn, if_exists='replace', index=False)
        print(f"✅ Successfully loaded {len(df_rest)} restaurants (with merged data).")

    except Exception as e:
        print(f"❌ Error loading restaurants: {e}")

    # --- 3. 旅館資料匯入 (Hotels.csv) ---
    try:
        hotel_path = os.path.join(DATA_DIR, 'Hotels.csv')
        df_hotel = pd.read_csv(hotel_path, encoding='utf-8-sig')
        df_hotel.columns = df_hotel.columns.str.strip()
        
        if 'HotelName' in df_hotel.columns: df_hotel.rename(columns={'HotelName': 'Name'}, inplace=True)
        if 'TypeName' in df_hotel.columns: df_hotel.rename(columns={'TypeName': 'Types'}, inplace=True)
        
        df_hotel.to_sql('hotels', conn, if_exists='replace', index=False)
        print(f"✅ Loaded {len(df_hotel)} hotels.")
    except Exception as e:
        print(f"❌ Error loading Hotels: {e}")

    # --- 4. 景點資料匯入 (Kyoto_attractions.csv) ---
    try:
        attr_path = os.path.join(DATA_DIR, 'Kyoto_attractions.csv')
        df_attr = pd.read_csv(attr_path, encoding='utf-8-sig')
        df_attr.columns = df_attr.columns.str.strip()
        
        if 'name' in df_attr.columns: df_attr.rename(columns={'name': 'Name'}, inplace=True)
        
        df_attr.to_sql('attractions', conn, if_exists='replace', index=False)
        print(f"✅ Loaded {len(df_attr)} attractions.")
    except Exception as e:
        print(f"❌ Error loading Attractions: {e}")

    conn.commit()
    conn.close()
    print("✨ Database Initialization Complete.")

# ==========================================
#  資料讀取函式 (Getters)
# ==========================================

# utils/database.py

def get_all_restaurants():
    """從數據庫獲取所有餐廳數據 (超級防呆版：補齊缺失欄位)"""
    # print(f"🔍 Reading Restaurants from: {DB_PATH}") 
    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. 讀取所有資料
        query = "SELECT * FROM restaurants" 
        df = pd.read_sql_query(query, conn)
        
        # 2. 🔥 [修復 1] 補齊評分欄位 (TotalRating)
        if 'TotalRating' not in df.columns:
            if 'Rating' in df.columns:
                df.rename(columns={'Rating': 'TotalRating'}, inplace=True)
            elif 'rating' in df.columns:
                df.rename(columns={'rating': 'TotalRating'}, inplace=True)
            else:
                print("⚠️ Warning: No rating column found. Creating default 0.")
                df['TotalRating'] = 0

        # 3. 🔥 [修復 2] 補齊分類欄位 (FirstCategory)
        # 這是導致地圖報錯的主因
        if 'FirstCategory' not in df.columns:
            if 'Category' in df.columns:
                df.rename(columns={'Category': 'FirstCategory'}, inplace=True)
            else:
                print("⚠️ Warning: No Category column found. Creating default 'Food'.")
                df['FirstCategory'] = 'Food'

        # 4. [修復 3] 補齊價格欄位 (避免 Analytics 報錯)
        if 'LunchPrice' not in df.columns: df['LunchPrice'] = None
        if 'DinnerPrice' not in df.columns: df['DinnerPrice'] = None

        # 5. 確保數值格式正確
        df['TotalRating'] = pd.to_numeric(df['TotalRating'], errors='coerce').fillna(0)
            
        # 6. 排序
        df = df.sort_values(by='TotalRating', ascending=False)
            
        return df
    except Exception as e:
        print(f"❌ Error getting restaurants: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_all_hotels():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM hotels", conn)
        
        # 1. 補齊 HotelName
        if 'HotelName' not in df.columns and 'Name' in df.columns:
             df.rename(columns={'Name': 'HotelName'}, inplace=True)
        
        # 2. 🔥 [修復 Types] 補齊類型欄位
        if 'Types' not in df.columns:
            if 'TypeName' in df.columns:
                df.rename(columns={'TypeName': 'Types'}, inplace=True)
            else:
                df['Types'] = 'Hotel'
        
        # 3. 轉成 List (前端卡片需要 List)
        def parse_types(val):
            if isinstance(val, list): return val
            if pd.isna(val): return ['Hotel']
            return [str(val)]
        df['Types'] = df['Types'].apply(parse_types)
        
        # 4. 補齊評分
        if 'Rating' in df.columns:
             df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0)
             
        return df
    except Exception as e:
        print(f"Error getting hotels: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_all_attractions():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM attractions", conn)
        # 經緯度清理
        df['Lat'] = pd.to_numeric(df['Lat'], errors='coerce')
        # 兼容 Lng 和 Long
        if 'Lng' in df.columns: df['Lng'] = pd.to_numeric(df['Lng'], errors='coerce')
        if 'Long' not in df.columns and 'Lng' in df.columns: df['Long'] = df['Lng']
        
        return df
    except Exception as e:
        print(f"Error getting attractions: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# 隨機獲取 N 個高分餐廳
def get_random_top_restaurants(n=5, min_rating=0):
    """
    隨機獲取高分餐廳 (改用 Pandas 處理，防止 SQL 報錯)
    """
    try:
        # 使用修復過的 get_all_restaurants 來獲取資料
        # 這裡面已經處理了欄位補齊和改名
        df = get_all_restaurants()
        
        if df.empty: return df

        # 篩選評分 (如果 min_rating > 0 且 TotalRating 欄位存在)
        if min_rating > 0 and 'TotalRating' in df.columns:
            df = df[df['TotalRating'] >= min_rating]
            
        # 隨機取樣
        if len(df) > n:
            return df.sample(n=n)
        return df
    except Exception as e:
        print(f"❌ Error in get_random_top_restaurants: {e}")
        return pd.DataFrame()

# 隨機獲取 N 個高分旅館
def get_random_top_hotels(n=5, min_rating=4.0):
    with get_db_connection() as conn:
        try:
            # 1. 讀取資料
            query = "SELECT * FROM hotels WHERE Rating >= ? ORDER BY RANDOM() LIMIT ?"
            df = pd.read_sql_query(query, conn, params=(min_rating, n))

            # 2. 補齊 HotelName
            if 'HotelName' not in df.columns and 'Name' in df.columns:
                 df.rename(columns={'Name': 'HotelName'}, inplace=True)

            # 3. 🔥 [修復 Types] 這就是導致你報錯的關鍵！
            # 必須確保 Types 欄位存在，且格式為 List
            if 'Types' not in df.columns:
                if 'TypeName' in df.columns:
                    df.rename(columns={'TypeName': 'Types'}, inplace=True)
                else:
                    df['Types'] = 'Hotel'

            # 強制轉型為 List
            def parse_types(val):
                if isinstance(val, list): return val
                if pd.isna(val): return ['Hotel']
                return [str(val)]
            df['Types'] = df['Types'].apply(parse_types)

            return df
        except Exception as e: 
            print(f"Error in get_random_top_hotels: {e}")
            return pd.DataFrame()

# 隨機獲取 N 個高分景點
def get_random_top_attractions(n=5, min_rating=0):
    """
    隨機獲取高分景點 (改用 Pandas 處理)
    """
    try:
        df = get_all_attractions()
        if df.empty: return df
        
        # 確保有 Rating 欄位，沒有補 0
        if 'Rating' not in df.columns: 
            df['Rating'] = 0
            
        if min_rating > 0:
            df = df[df['Rating'] >= min_rating]
            
        if len(df) > n:
            return df.sample(n=n)
        return df
    except Exception as e:
        print(f"❌ Error in get_random_top_attractions: {e}")
        return pd.DataFrame()

# ==========================================
#  功能函式 (Search, Get by ID, Favorites)
# ==========================================

def get_restaurant_by_id(rid):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM restaurants WHERE Restaurant_ID = ?", (rid,)).fetchone()
        return dict(row) if row else None

def get_hotel_by_id(hid):
    with get_db_connection() as conn:
        # 嘗試匹配 Hotel_ID 或 ID
        row = conn.execute("SELECT * FROM hotels WHERE Hotel_ID = ?", (hid,)).fetchone()
        if not row: # Try just 'ID' column if Hotel_ID doesn't exist
             try: row = conn.execute("SELECT * FROM hotels WHERE ID = ?", (hid,)).fetchone()
             except: pass
        
        if row:
            d = dict(row)
            if 'Types' not in d: d['Types'] = ['Hotel']
            else: d['Types'] = [d['Types']]
            if 'HotelName' not in d and 'Name' in d: d['HotelName'] = d['Name']
            return d
        return None

def get_attraction_by_id(aid):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM attractions WHERE ID = ?", (aid,)).fetchone()
        return dict(row) if row else None

def toggle_favorite_db(user_id, item_id, item_type):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM Favorites WHERE user_id=? AND item_id=? AND item_type=?", (user_id, str(item_id), item_type))
        if c.fetchone():
            c.execute("DELETE FROM Favorites WHERE user_id=? AND item_id=? AND item_type=?", (user_id, str(item_id), item_type))
            conn.commit()
            return False
        else:
            c.execute("INSERT INTO Favorites (user_id, item_id, item_type) VALUES (?, ?, ?)", (user_id, str(item_id), item_type))
            conn.commit()
            return True

def get_user_favorites(user_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM Favorites WHERE user_id=?", (user_id,))
        rows = c.fetchall()
        
    favs = {'Restaurant': [], 'Hotel': [], 'Attraction': []}
    for row in rows:
        if row['item_type'] in favs:
            favs[row['item_type']].append(row['item_id'])
    return favs

# [修復] 搜尋餐廳：改用 Pandas 篩選，避開 SQL 欄位名稱錯誤
def search_restaurants(keyword=None, cuisine=None, rating=None, price_range=None, min_reviews=None, stations=None, sort_by='rating_desc'):
    """
    搜尋餐廳 (Pandas 版 - 防止 SQL 欄位錯誤)
    """
    try:
        # 1. 重用我們已經修復好的 get_all_restaurants
        df = get_all_restaurants()
        
        if df.empty: return df

        # 2. 關鍵字搜尋
        if keyword:
            kw = keyword.lower()
            mask = pd.Series(False, index=df.index)
            
            if 'Name' in df.columns:
                mask |= df['Name'].str.lower().str.contains(kw, na=False)
            if 'JapaneseName' in df.columns:
                mask |= df['JapaneseName'].str.lower().str.contains(kw, na=False)
            
            df = df[mask]

        # 3. 料理類型
        if cuisine:
            target_col = None
            if 'SecondCategory' in df.columns: target_col = 'SecondCategory'
            elif 'FirstCategory' in df.columns: target_col = 'FirstCategory'
            
            if target_col:
                df = df[df[target_col] == cuisine]

        # 4. 評分篩選
        if rating:
            try:
                if isinstance(rating, str) and '-' in rating:
                    min_r, max_r = map(float, rating.split('-'))
                    df = df[(df['TotalRating'] >= min_r) & (df['TotalRating'] <= max_r)]
                else:
                    min_r = float(rating)
                    df = df[df['TotalRating'] >= min_r]
            except: pass

        # 5. 排序邏輯
        if sort_by == 'rating_desc':
            df = df.sort_values('TotalRating', ascending=False)
        elif sort_by == 'reviews_desc' and 'ReviewNum' in df.columns:
            df = df.sort_values('ReviewNum', ascending=False)
        elif sort_by == 'name_asc' and 'Name' in df.columns:
            df = df.sort_values('Name', ascending=True)
        
        return df

    except Exception as e:
        print(f"❌ Error in search_restaurants: {e}")
        return pd.DataFrame()
    
# 搜尋旅館
def search_hotels(keyword=None, hotel_type=None, min_rating=None, sort_by='rating_desc'):
    with get_db_connection() as conn:
        query = "SELECT * FROM hotels WHERE 1=1"
        params = []
        if keyword:
            # 這裡也要用 Name 或 HotelName
            query += " AND (Name LIKE ? OR Address LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        if sort_by == 'rating_desc': query += " ORDER BY Rating DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        
        # 後處理 (跟上面一樣的防呆邏輯)
        if 'HotelName' not in df.columns and 'Name' in df.columns:
             df.rename(columns={'Name': 'HotelName'}, inplace=True)
             
        if 'Types' not in df.columns: df['Types'] = 'Hotel'
        df['Types'] = df['Types'].apply(lambda x: [str(x)] if not isinstance(x, list) else x)
        
        return df

# 搜尋景點
def search_attractions(keyword=None, attr_type=None, min_rating=None, max_rating=None, sort_by='rating_desc'):
    """搜尋景點 (Pandas 版)"""
    try:
        df = get_all_attractions()
        if df.empty: return df

        if keyword:
            kw = keyword.lower()
            if 'Name' in df.columns:
                df = df[df['Name'].str.lower().str.contains(kw, na=False)]

        if sort_by == 'rating_desc' and 'Rating' in df.columns:
            df = df.sort_values('Rating', ascending=False)

        return df
    except Exception:
        return pd.DataFrame()

# 取得唯一值 (Dropdown 用)
def get_unique_cuisines():
    with get_db_connection() as conn:
        try:
            q = "SELECT DISTINCT SecondCategory FROM restaurants WHERE SecondCategory IS NOT NULL ORDER BY SecondCategory"
            return [r[0] for r in conn.execute(q).fetchall()]
        except: return []

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

def get_unique_hotel_types():
    with get_db_connection() as conn:
        # 因為我們把 Types 簡化存入，這裡可能只能撈到單一值，或是需要從 CSV 讀 Types.csv
        # 為了簡單，回傳固定列表或從 table 撈
        try:
            q = "SELECT DISTINCT TypeName FROM hotels" # 如果你之前的 csv 有這個欄位
            return [r[0] for r in conn.execute(q).fetchall()]
        except: return ['Hotel', 'Ryokan', 'Hostel'] # Fallback

def get_unique_attraction_types():
    with get_db_connection() as conn:
        try:
            q = "SELECT DISTINCT Type FROM attractions WHERE Type IS NOT NULL ORDER BY Type"
            return [r[0] for r in conn.execute(q).fetchall()]
        except: return []
        
# 你的其他輔助函式 (Nearby 等)
def get_nearby_restaurants(lat, long, limit=5, exclude_id=None):
    # 簡化版：使用 SQL 計算 (SQLite 不支援高階數學，這裡用 Python 算)
    df = get_all_restaurants()
    if df.empty or lat is None or long is None: return []
    
    def dist(row):
        return math.sqrt((row['Lat']-lat)**2 + (row['Long']-long)**2)
    
    df['distance'] = df.apply(dist, axis=1)
    df = df.sort_values('distance')
    if exclude_id: df = df[df['Restaurant_ID'] != exclude_id]
    
    # 轉換回 km (粗略估計 1度約111km)
    df['distance'] = df['distance'] * 111 
    return df.head(limit).to_dict('records')

def get_nearby_hotels(lat, long, limit=5, exclude_id=None):
    df = get_all_hotels()
    if df.empty or lat is None or long is None: return []
    def dist(row): return math.sqrt((row['Lat']-lat)**2 + (row['Long']-long)**2)
    df['distance'] = df.apply(dist, axis=1) * 111
    df = df.sort_values('distance')
    if exclude_id: df = df[df['Hotel_ID'] != exclude_id]
    return df.head(limit).to_dict('records')

# Analytics (模擬)
def get_combined_analytics_data():
    # 回傳整合的 DataFrame (餐廳+旅館+景點)
    df_r = get_all_restaurants()
    df_h = get_all_hotels()
    df_a = get_all_attractions()
    
    res = []
    for _, r in df_r.iterrows():
        res.append({'ID': r['Restaurant_ID'], 'Name': r['Name'], 'Type': 'Restaurant', 'Lat': r['Lat'], 'Long': r['Long'], 'Rating': r['TotalRating'], 'Price': 2000})
    for _, h in df_h.iterrows():
        res.append({'ID': h['Hotel_ID'], 'Name': h['HotelName'], 'Type': 'Hotel', 'Lat': h['Lat'], 'Long': h['Long'], 'Rating': h['Rating'], 'Price': 8000})
    for _, a in df_a.iterrows():
        res.append({'ID': a['ID'], 'Name': a['Name'], 'Type': 'Attraction', 'Lat': a['Lat'], 'Long': a['Long'], 'Rating': a['Rating'], 'Price': 0})
        
    return pd.DataFrame(res)

# 用來避免 import 錯誤的空函式
def init_new_tables(): pass 
def get_revenue_trend(id): return pd.DataFrame()
def get_occupancy_status(id): return pd.DataFrame()

# ==========================================
# 🔥 補回遺失的輔助函式 (請貼在 utils/database.py 最下方)
# ==========================================

def get_restaurants_by_category(rating_category: str) -> pd.DataFrame:
    """根據評分類別獲取餐廳 (例如 '4~5 星餐廳')"""
    with get_db_connection() as conn:
        try:
            # 嘗試直接查詢 Rating_Category 欄位
            query = "SELECT * FROM restaurants WHERE Rating_Category = ?"
            df = pd.read_sql_query(query, conn, params=(rating_category,))
            return df
        except Exception:
            # 如果資料庫沒有這個欄位，我們手動用 TotalRating 篩選
            query = "SELECT * FROM restaurants"
            df = pd.read_sql_query(query, conn)
            if 'TotalRating' in df.columns:
                if '4~5' in rating_category:
                    return df[df['TotalRating'] >= 4]
                elif '3~4' in rating_category:
                    return df[(df['TotalRating'] >= 3) & (df['TotalRating'] < 4)]
            return pd.DataFrame()

def get_restaurant_count() -> int:
    """獲取餐廳總數"""
    with get_db_connection() as conn:
        try:
            return conn.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
        except:
            return 0

def get_top_rated_restaurants(limit: int = 10, min_reviews: int = 10) -> pd.DataFrame:
    """獲取評分最高的餐廳"""
    with get_db_connection() as conn:
        try:
            query = """
                SELECT * FROM restaurants 
                WHERE ReviewNum >= ? 
                ORDER BY TotalRating DESC 
                LIMIT ?
            """
            return pd.read_sql_query(query, conn, params=(min_reviews, limit))
        except:
            return pd.DataFrame()

def get_booking_data(hotel_id=None):
    """讀取訂房數據 (用於分析圖表)"""
    try:
        csv_path = os.path.join(DATA_DIR, 'bookings.csv')
        if not os.path.exists(csv_path): return pd.DataFrame()
        
        df = pd.read_csv(csv_path, parse_dates=['booking_date', 'check_in_date'])
        if hotel_id is not None:
            df = df[df['hotel_id'] == int(hotel_id)]
        return df
    except:
        return pd.DataFrame()

def get_revenue_trend(hotel_id=None):
    """營收趨勢"""
    df = get_booking_data(hotel_id)
    if df.empty: return pd.DataFrame()
    df = df[df['status'] == 'Confirmed']
    df['Month'] = df['check_in_date'].dt.to_period('M').astype(str)
    return df.groupby('Month')['price_paid'].sum().reset_index().rename(columns={'price_paid': 'Revenue'})

def get_occupancy_status(hotel_id=None):
    """入住狀態"""
    df = get_booking_data(hotel_id)
    if df.empty: return pd.DataFrame()
    df['Month'] = df['check_in_date'].dt.to_period('M').astype(str)
    return df.groupby(['Month', 'status']).size().reset_index(name='Count')

def get_market_analysis_data():
    """市場分析數據 (為了相容舊版 app.py)"""
    # 簡單回傳所有旅館數據，避免報錯
    return get_all_hotels()

def get_hotels_by_type(type_name: str) -> pd.DataFrame:
    """根據類型獲取旅館列表 (修復 ImportError)"""
    try:
        df = get_all_hotels()
        if df.empty: return pd.DataFrame()
        
        # 篩選邏輯：檢查該旅館的 Types 列表是否包含指定的 type_name
        # 注意：get_all_hotels 已經確保 'Types' 是一個 list
        filtered_df = df[df['Types'].apply(lambda types: type_name in types)]
        
        return filtered_df
    except Exception as e:
        print(f"Error filtering hotels by type: {e}")
        return pd.DataFrame()

def get_unique_hotel_types() -> List[str]:
    """獲取所有不重複的旅館類型 (用於下拉選單)"""
    try:
        df = get_all_hotels()
        if df.empty: return ['Hotel']
        
        # 收集所有出現過的類型
        unique_types = set()
        for types_list in df['Types']:
            if isinstance(types_list, list):
                unique_types.update(types_list)
            else:
                unique_types.add(str(types_list))
                
        return sorted(list(unique_types))
    except Exception:
        return ['Hotel', 'Ryokan', 'Hostel'] # 發生錯誤時的回傳預設值