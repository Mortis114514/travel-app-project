import requests
import csv
import time
import json
from urllib.parse import urlencode

# 根據您的截圖，這是正確的 ApplicationID
APP_ID = "1046226217348773409" 

# 楽天旅遊簡單旅館搜尋 API 端點
URL = "https://app.rakuten.co.jp/services/api/Travel/SimpleHotelSearch/20170426"

def fetch_page(page):
    """根據頁碼發送 API 請求，同時使用地區代碼和經緯度"""
    params = {
        "applicationId": APP_ID,
        "format": "json",
        
        # 策略 1: 地區代碼 (largeClassCode=26 代表京都府)
        "largeClassCode": "26", 
        
        # 策略 2: 經緯度座標 (京都市中心)
        "latitude": 35.0116,          # 緯度
        "longitude": 135.7681,        # 經度
        "searchRadius": 15,           # 半徑 15km
        "datumType": 1,               # 經緯度標準 (WGS84)
        
        "hits": 30,                   # 每頁筆數
        "page": page,
    }
    
    # 打印完整的請求 URL，方便除錯
    request_url = f"{URL}?{urlencode(params)}"
    print(f"DEBUG: 正在請求的 URL: {request_url}")

    try:
        # 使用 timeout 避免請求卡住
        res = requests.get(URL, params=params, timeout=10)
        
        if res.status_code != 200:
            print(f"❌ API 請求失敗，狀態碼: {res.status_code}")
            return {}
        
        data = res.json()
        
        # 檢查 API 是否返回了錯誤訊息 (如果狀態碼是 200，但內容是錯誤)
        if data.get("error"):
            print(f"❌ 內部 API 錯誤: {data['error_description']}")
            return {}
            
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 發生連線錯誤: {e}")
        return {}


def main():
    """主執行函式：循環抓取所有頁面並寫入 CSV"""
    output = []
    page = 1
    max_pages = 5 # 限制最多抓取頁數

    print("🚀 開始使用雙重參數驗證抓取楽天旅遊京都住宿資料...")

    while page <= max_pages:
        data = fetch_page(page)

        # 檢查是否為空的字典 (請求失敗或連線錯誤)
        if not data:
            break
            
        # 檢查 hotels 欄位是否存在且不為空
        if "hotels" not in data or not data["hotels"]:
            print("✅ 已達最後一頁或無資料可抓取。")
            break

        hotels = data["hotels"]
        print(f"📚 成功抓到第 {page} 頁，共 {len(hotels)} 筆資料")

        for h in hotels:
            if len(h.get("hotel", [])) > 0:
                info = h["hotel"][0].get("hotelBasicInfo", {})
                
                output.append([
                    info.get("hotelNo"),
                    info.get("hotelName"),
                    info.get("hotelKanaName"),
                    info.get("hotelGrade"),
                    info.get("reviewAverage"),
                    info.get("address1", "") + " " + info.get("address2", ""),
                    info.get("latitude"),
                    info.get("longitude"),
                    info.get("hotelMinCharge")
                ])

        page += 1
        time.sleep(0.3)

    # 寫入 CSV
    if not output:
        print("⚠️ 最終確認：未抓到任何資料。如果 ID 有效，這可能是 API 服務器端的問題。")
    else:
        file_path = "kyoto_hotels.csv"
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "HotelID", "HotelName", "HotelKana", "StarRating",
                "ReviewAverage", "Address", "Latitude", "Longitude", "MinPrice"
            ])
            writer.writerows(output)
        print(f"✅ 完成！共抓取 {len(output)} 筆資料，已生成 {file_path}")

if __name__ == "__main__":
    main()