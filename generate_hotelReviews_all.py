import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid
import csv
import os

# --- 設定路徑 ---
# 請確保你的專案根目錄下有 data 資料夾，且裡面有 Hotels.csv
DATA_DIR = 'data'
HOTELS_PATH = os.path.join(DATA_DIR, 'Hotels.csv')
BOOKINGS_OUTPUT = os.path.join(DATA_DIR, 'bookings.csv')
REVIEWS_OUTPUT = os.path.join(DATA_DIR, 'HotelReviews.csv')

# --- 評論生成設定 (Phrase Pools) ---
OPENINGS = ["The stay was", "I found the hotel", "Overall it was", "We had a", "My experience was"]
ASPECTS = ["room", "service", "location", "breakfast", "cleanliness", "staff", "value"]
ADJ_POS = ["excellent", "fantastic", "very good", "pleasant", "comfortable", "impressive"]
ADJ_NEU = ["okay", "average", "fine", "acceptable"]
ADJ_NEG = ["disappointing", "poor", "below expectations", "terrible"]
ENDINGS = [". Would stay again.", ". Recommended for the price.", ". Friendly staff.", ". A convenient choice.", ". Not much to complain about."]
SPECIFIC_REVIEWS = [
    "Great breakfast selection.", "The bed was very comfortable.", "Amazing view from the room.", 
    "Close to public transport.", "早餐豐富且美味。", "部屋からの眺めが最高でした。", 
    "The housekeeping was quick.", "Helpful front desk service."
]

# 中日文片語庫
CN_OPENINGS = ["住宿體驗", "整體來說", "這次入住", "感覺是", "個人覺得"]
CN_ASPECTS = ["房間", "服務", "地點", "早餐", "整潔度", "員工", "性價比"]
CN_POS = ["很棒", "不錯", "舒適", "令人滿意"]
CN_NEU = ["一般", "還可以", "普通"]
CN_NEG = ["失望", "不佳", "需要改進"]
CN_ENDINGS = ["，會再入住。", "，值得推薦。", "，方便。", "，還可以。"]

JP_OPENINGS = ["滞在は", "全体的に", "今回の宿泊は", "個人的には", "感想としては"]
JP_ASPECTS = ["部屋", "サービス", "立地", "朝食", "清潔さ", "スタッフ", "コスパ"]
JP_POS = ["素晴らしい", "快適", "満足しました", "良い"]
JP_NEU = ["普通", "まあまあ", "可もなく不可もなく"]
JP_NEG = ["期待外れ", "不満", "改善が必要"]
JP_ENDINGS = ["。また泊まりたいです。", "。おすすめします。", "。便利です。"]

def compose_comment(rating, lang='en'):
    """根據評分和語言組裝評論"""
    if random.random() < 0.15: return random.choice(SPECIFIC_REVIEWS)
    
    if lang == 'en':
        opener, aspect = random.choice(OPENINGS), random.choice(ASPECTS)
        if rating >= 4: adj, end = random.choice(ADJ_POS), random.choice(ENDINGS)
        elif rating == 3: adj, end = random.choice(ADJ_NEU), random.choice([".", random.choice(ENDINGS)])
        else: adj, end = random.choice(ADJ_NEG), random.choice([".", ". Would not recommend."])
        core = f"{opener} {adj} regarding the {aspect}"
    elif lang == 'cn':
        opener, aspect = random.choice(CN_OPENINGS), random.choice(CN_ASPECTS)
        if rating >= 4: adj, end = random.choice(CN_POS), random.choice(CN_ENDINGS)
        elif rating == 3: adj, end = random.choice(CN_NEU), "。"
        else: adj, end = random.choice(CN_NEG), "，不推薦。"
        core = f"{opener}{adj}，關於{aspect}"
    else: # jp
        opener, aspect = random.choice(JP_OPENINGS), random.choice(JP_ASPECTS)
        if rating >= 4: adj, end = random.choice(JP_POS), random.choice(JP_ENDINGS)
        elif rating == 3: adj, end = random.choice(JP_NEU), "。"
        else: adj, end = random.choice(JP_NEG), "。おすすめしません。"
        core = f"{opener}{adj}、{aspect}について"
        
    return f"{core}{end}"

def generate_all_data():
    print(f"Loading hotels from {HOTELS_PATH}...")
    try:
        hotels_df = pd.read_csv(HOTELS_PATH)
        # 確保 Hotel_ID 為數值格式
        hotels_df['Hotel_ID'] = pd.to_numeric(hotels_df['Hotel_ID'], errors='coerce')
        hotels_df = hotels_df.dropna(subset=['Hotel_ID'])
        hotel_ids = hotels_df['Hotel_ID'].unique()
        print(f"Found {len(hotel_ids)} hotels.")
    except FileNotFoundError:
        print(f"Error: {HOTELS_PATH} not found.")
        return

    bookings_data = []
    reviews_data = []
    review_id_counter = 1
    
    room_types = ['Double', 'Suite', 'Single', 'Family', 'King', 'Queen']
    statuses = ['Confirmed', 'Cancelled']
    
    # 時間設定
    today = datetime.now()
    end_date = today + timedelta(days=180)
    start_date = today - timedelta(days=730) # 過去兩年
    total_days = (end_date - start_date).days

    print("Generating bookings and reviews for each hotel...")
    
    for _, hotel in hotels_df.iterrows():
        hotel_id = int(hotel['Hotel_ID'])
        
        # 1. 決定這家飯店的「熱門程度」 (Popularity Factor)
        # 熱門的飯店訂單多，評論也多，這樣數據才合理
        popularity = random.uniform(0.5, 2.0) 
        
        # 2. 生成訂單 (Bookings)
        num_bookings = int(random.randint(50, 200) * popularity)
        
        # 取得飯店真實評分作為基準
        try:
            base_rating = float(hotel.get('Rating', 4.0))
            if pd.isna(base_rating): base_rating = 4.0
        except:
            base_rating = 4.0

        # 生成這家飯店的訂單
        for _ in range(num_bookings):
            # 隨機日期
            days_offset = random.randint(0, total_days)
            check_in_date = start_date + timedelta(days=days_offset)
            booking_date = check_in_date - timedelta(days=random.randint(1, 60))
            
            # 價格波動
            month = check_in_date.month
            base_price = 12000 if month not in [3, 4, 11] else 18000
            price_paid = round(base_price * random.uniform(0.8, 1.5), 0)
            
            status = random.choices(statuses, weights=[0.85, 0.15], k=1)[0]
            final_price = 0 if status == 'Cancelled' else price_paid
            
            booking_uuid = str(uuid.uuid4())
            
            bookings_data.append({
                'booking_id': booking_uuid,
                'hotel_id': hotel_id,
                'booking_date': booking_date.strftime('%Y-%m-%d'),
                'check_in_date': check_in_date.strftime('%Y-%m-%d'),
                'price_paid': final_price,
                'status': status,
                'room_type': random.choice(room_types)
            })
            
            # 3. 生成評論 (Reviews) - 連動邏輯
            # 只有「已確認」且「日期在過去」的訂單才可能會有評論
            if status == 'Confirmed' and check_in_date < today:
                # 評論轉換率 (約 30% 的人會寫評論)
                if random.random() < 0.3:
                    # 評分邏輯：基於飯店真實評分做常態分佈波動
                    rating = int(round(np.random.normal(base_rating, 0.8)))
                    rating = max(1, min(5, rating)) # 限制在 1-5 分
                    
                    # 決定語言
                    lang_rand = random.random()
                    lang = 'en' if lang_rand < 0.6 else ('cn' if lang_rand < 0.85 else 'jp')
                    
                    comment = compose_comment(rating, lang)
                    
                    reviews_data.append({
                        'Review_ID': review_id_counter,
                        'Hotel_ID': hotel_id,
                        'Review_Text': comment,
                        'Review_Rating': rating,
                        'Review_Date': (check_in_date + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'), # 評論通常在入住後幾天寫
                        'Booking_ID': booking_uuid # 關聯訂單 ID (進階分析可用)
                    })
                    review_id_counter += 1

    # --- 儲存檔案 ---
    if bookings_data:
        df_bookings = pd.DataFrame(bookings_data)
        df_bookings.sort_values('check_in_date', inplace=True)
        # 確保目錄存在
        os.makedirs(DATA_DIR, exist_ok=True)
        df_bookings.to_csv(BOOKINGS_OUTPUT, index=False)
        print(f"✅ Generated {len(df_bookings)} bookings -> {BOOKINGS_OUTPUT}")
    
    if reviews_data:
        df_reviews = pd.DataFrame(reviews_data)
        df_reviews.sort_values('Review_Date', inplace=True)
        df_reviews.to_csv(REVIEWS_OUTPUT, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
        print(f"✅ Generated {len(df_reviews)} reviews -> {REVIEWS_OUTPUT}")

if __name__ == '__main__':
    generate_all_data()