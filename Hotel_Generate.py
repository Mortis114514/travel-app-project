import pandas as pd
import requests
import time

API_KEY = "AIzaSyAMc4KPATogfZlGj7qpir34DyHFWjszKwU"

# 讀入剛剛的基本資料 CSV
df = pd.read_csv("Kyoto_Hotels_Google.csv")

# 新增欄位
df["PhoneNumber"] = ""
df["Website"] = ""
df["StarRating"] = ""
df["GoogleMapURL"] = ""

details_url = "https://maps.googleapis.com/maps/api/place/details/json"

for i, row in df.iterrows():
    pid = row["Place_ID"]
    params = {
        "place_id": pid,
        "fields": "name,formatted_phone_number,website,url,hotel_star_rating",
        "key": API_KEY,
        "language": "ja"
    }

    res = requests.get(details_url, params=params)
    data = res.json()

    if "result" in data:
        result = data["result"]
        df.at[i, "PhoneNumber"] = result.get("formatted_phone_number", "")
        df.at[i, "Website"] = result.get("website", "")
        df.at[i, "StarRating"] = result.get("hotel_star_rating", "")
        df.at[i, "GoogleMapURL"] = result.get("url", "")

    print(f"🏨 ({i+1}/{len(df)}) {row['HotelName']} 詳細資料抓取完成")
    time.sleep(0.3)  # 避免觸發速率限制

# 匯出完整資料
df.to_csv("Kyoto_Hotels_Detailed.csv", index=False, encoding="utf-8-sig")
print("✅ 飯店詳細資料已匯出：Kyoto_Hotels_Detailed.csv")
