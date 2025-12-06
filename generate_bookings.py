import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid

def generate_booking_data():
    """
    生成模擬訂單數據，確保每家飯店都有資料，且數據量足夠畫出漂亮的圖。
    """
    try:
        hotels_df = pd.read_csv('data/Hotels.csv')
        hotel_ids = hotels_df['Hotel_ID'].dropna().unique()
        print(f"Found {len(hotel_ids)} hotels. Generating data...")
    except FileNotFoundError:
        print("Error: 'data/Hotels.csv' not found.")
        return pd.DataFrame()

    data = []
    room_types = ['Double', 'Suite', 'Single', 'Family', 'King', 'Queen']
    statuses = ['Confirmed', 'Cancelled']
    
    # 設定時間範圍：過去一年 ~ 未來半年
    end_date = datetime.now() + timedelta(days=180)
    start_date = datetime.now() - timedelta(days=365) 
    total_days = (end_date - start_date).days

    # --- 核心修改：針對「每一家」飯店生成數據 ---
    for hotel_id in hotel_ids:
        
        # 每家飯店生成 50 ~ 150 筆訂單 (讓圖表看起來豐富一點)
        num_bookings_for_this_hotel = random.randint(50, 150)
        
        for _ in range(num_bookings_for_this_hotel):
            # 隨機日期
            days_offset = random.randint(0, total_days)
            check_in_date = start_date + timedelta(days=days_offset)
            
            # 提前 1~60 天預訂
            booking_date = check_in_date - timedelta(days=random.randint(1, 60))
            
            # 模擬價格 (依據淡旺季波動)
            month = check_in_date.month
            base_price = 12000
            if month in [3, 4, 11]: # 旺季價格高
                base_price = 18000
            
            price_paid = round(base_price * random.uniform(0.8, 1.5), 0)
            
            # 85% 機率確認，15% 機率取消
            status = random.choices(statuses, weights=[0.85, 0.15], k=1)[0]
            
            # 如果取消，營收歸零
            final_price = 0 if status == 'Cancelled' else price_paid

            data.append({
                'booking_id': str(uuid.uuid4()),
                'hotel_id': hotel_id,
                'booking_date': booking_date.strftime('%Y-%m-%d'),
                'check_in_date': check_in_date.strftime('%Y-%m-%d'),
                'price_paid': final_price,
                'status': status,
                'room_type': random.choice(room_types)
            })

    # 轉成 DataFrame
    df = pd.DataFrame(data)
    # 按日期排序
    df = df.sort_values('check_in_date')
    return df

if __name__ == '__main__':
    print("Starting data generation...")
    bookings_df = generate_booking_data()
    
    if not bookings_df.empty:
        try:
            bookings_df.to_csv('data/bookings.csv', index=False)
            print(f"🎉 Successfully generated {len(bookings_df)} bookings in 'data/bookings.csv'")
            print("Now every hotel has data!")
        except Exception as e:
            print(f"Error saving to CSV: {e}")