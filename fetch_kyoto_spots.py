import requests
import pandas as pd
import time
import csv

# ==========================================
# 1. 設定區
# ==========================================
API_KEY = "AIzaSyAMc4KPATogfZlGj7qpir34DyHFWjszKwU"  # 🔴 請在這裡貼上你的 Google API Key
OUTPUT_FILE = "data/kyoto_attractions.csv"

# 我們要搜尋的關鍵字列表，以確保覆蓋度夠廣
SEARCH_QUERIES = [
    "Kyoto historical sites",   # 京都 古蹟
    "Kyoto temples",            # 京都 寺廟
    "Kyoto shrines",            # 京都 神社
    "Kyoto museums",            # 京都 博物館
    "Kyoto tourist attractions" # 京都 觀光景點
]

def get_places_data(api_key, queries):
    all_places = {} # 使用 Dictionary 去重 (以 place_id 為 key)
    
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    for query in queries:
        print(f"🔍 Searching for: {query}...")
        params = {
            "query": query,
            "key": api_key,
            "language": "en" # 建議用英文取類別(Type)比較好做圖表，名稱可用日文或英文
        }
        
        while True:
            try:
                response = requests.get(url, params=params)
                data = response.json()
                
                if data.get("status") != "OK":
                    print(f"Error or no results for {query}: {data.get('status')}")
                    break

                for result in data.get("results", []):
                    place_id = result.get("place_id")
                    
                    # 避免重複抓取相同的景點
                    if place_id in all_places:
                        continue
                        
                    # 提取適合做圖表的資料
                    # 處理 Types: 只取第一個最有意義的類型，並排除通用詞
                    raw_types = result.get("types", [])
                    ignored_types = ['point_of_interest', 'establishment', 'tourist_attraction']
                    primary_type = next((t for t in raw_types if t not in ignored_types), raw_types[0] if raw_types else "unknown")
                    
                    place_info = {
                        "Place_ID": place_id,
                        "Name": result.get("name"),
                        "Rating": result.get("rating", 0), # 數值：做分佈圖用
                        "UserRatingsTotal": result.get("user_ratings_total", 0), # 數值：做氣泡圖大小用
                        "Type": primary_type.replace('_', ' ').title(), # 類別：做圓餅圖用
                        "PriceLevel": result.get("price_level", None), # 數值：做預算分析 (景點可能常是 None)
                        "Lat": result.get("geometry", {}).get("location", {}).get("lat"),
                        "Lng": result.get("geometry", {}).get("location", {}).get("lng"),
                        "Address": result.get("formatted_address")
                    }
                    all_places[place_id] = place_info

                # 處理分頁 (Google API 一頁 20 筆，最多 3 頁)
                page_token = data.get("next_page_token")
                if not page_token:
                    break
                
                # Google 要求在請求下一頁前必須等待幾秒
                params["pagetoken"] = page_token
                print("   ...fetching next page...")
                time.sleep(2) 
                
            except Exception as e:
                print(f"Exception occurred: {e}")
                break
                
    return list(all_places.values())

def save_to_csv(data, filename):
    if not data:
        print("No data found.")
        return

    # 轉成 DataFrame 方便處理
    df = pd.DataFrame(data)
    
    # 加入自定義 ID (從 1 開始)
    df.insert(0, 'ID', range(1, 1 + len(df)))
    
    # 存檔
    df.to_csv(filename, index=False, encoding='utf-8-sig') # sig 確保 Excel 打開不會亂碼
    print(f"✅ Successfully saved {len(df)} spots to {filename}")

# ==========================================
# 主程式
# ==========================================
if __name__ == "__main__":
    print("🚀 Starting Kyoto Data Collection...")
    places_data = get_places_data(API_KEY, SEARCH_QUERIES)
    save_to_csv(places_data, OUTPUT_FILE)