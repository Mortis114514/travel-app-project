import requests
import pandas as pd
import time

API_KEY = "AIzaSyAMc4KPATogfZlGj7qpir34DyHFWjszKwU"  # ← 請貼上剛剛拿到的金鑰

# 京都市中心（四条通附近）
latitude = 35.0116
longitude = 135.7681
radius = 3000  # 3公里範圍內搜尋飯店

url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

params = {
    "location": f"{latitude},{longitude}",
    "radius": radius,
    "type": "lodging",  # 尋找住宿類型
    "key": API_KEY,
    "language": "ja"  # 回傳日文名稱
}

hotels = []
page = 1

while True:
    print(f"📍 抓取第 {page} 頁資料...")
    res = requests.get(url, params=params)
    data = res.json()

    for result in data.get("results", []):
        hotels.append({
            "HotelName": result.get("name", ""),
            "Address": result.get("vicinity", ""),
            "Rating": result.get("rating", ""),
            "UserRatingsTotal": result.get("user_ratings_total", ""),
            "Types": ", ".join(result.get("types", [])),  # 類型清單
            "Lat": result["geometry"]["location"]["lat"],
            "Long": result["geometry"]["location"]["lng"],
            "Place_ID": result.get("place_id", "")
        })

    # 檢查是否有下一頁
    if "next_page_token" in data:
        next_token = data["next_page_token"]
        params["pagetoken"] = next_token
        page += 1
        time.sleep(2)  # 等待 token 生效
    else:
        break

# 匯出 CSV
df = pd.DataFrame(hotels)
df.to_csv("Kyoto_Hotels_Google.csv", index=False, encoding="utf-8-sig")

print(f"✅ 匯出完成，共 {len(df)} 筆資料。已儲存為 Kyoto_Hotels_Google.csv")

