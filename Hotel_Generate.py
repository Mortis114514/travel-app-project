import requests
import pandas as pd
import time

API_KEY = "AIzaSyAMc4KPATogfZlGj7qpir34DyHFWjszKwU"

# 京都中心座標（四条通附近）
center_lat, center_lng = 35.0116, 135.7681

# 分區設定（約 2 公里一格）
lat_steps = [-0.04, -0.02, 0, 0.02, 0.04]
lng_steps = [-0.04, -0.02, 0, 0.02, 0.04]

radius = 2000  # 2 公里
base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

all_hotels = {}
req_count = 0

for dlat in lat_steps:
    for dlng in lng_steps:
        lat = center_lat + dlat
        lng = center_lng + dlng

        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": "lodging",
            "key": API_KEY,
            "language": "ja"
        }

        page = 1
        while True:
            req_count += 1
            print(f"📍 抓取區塊 ({lat:.4f},{lng:.4f}) 第 {page} 頁，已用 {req_count} 次 API...")

            res = requests.get(base_url, params=params)
            data = res.json()

            if "results" not in data:
                print("⚠️ 發生錯誤：", data)
                break

            for r in data["results"]:
                pid = r.get("place_id")
                if pid not in all_hotels:  # 避免重複
                    all_hotels[pid] = {
                        "HotelName": r.get("name", ""),
                        "Address": r.get("vicinity", ""),
                        "Rating": r.get("rating", ""),
                        "UserRatingsTotal": r.get("user_ratings_total", ""),
                        "Types": ", ".join(r.get("types", [])),
                        "Lat": r["geometry"]["location"]["lat"],
                        "Lng": r["geometry"]["location"]["lng"],
                        "Place_ID": pid
                    }

            # 是否有下一頁
            if "next_page_token" in data:
                params["pagetoken"] = data["next_page_token"]
                page += 1
                time.sleep(2)  # token 延遲生效
            else:
                break

        time.sleep(1)  # 降低請求頻率避免配額問題

# 匯出 CSV
df = pd.DataFrame(list(all_hotels.values()))
df.to_csv("Kyoto_Hotels_Google.csv", index=False, encoding="utf-8-sig")

print(f"✅ 匯出完成，共 {len(df)} 筆資料。總共使用 API {req_count} 次。")
