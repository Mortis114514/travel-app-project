import pandas as pd

# 讀取資料
restaurants = pd.read_csv("Kyoto_Restaurant_Info.csv")
reviews = pd.read_csv("Reviews.csv")

# 將相同餐廳的評論彙整
reviews_grouped = (
    reviews.groupby("Restaurant_ID")
    .agg({
        "Review_Text": lambda x: " | ".join(x),  # 把多筆評論接成一個字串
        "Review_Rating": "mean"  # 計算平均評論星等
    })
    .reset_index()
)

# 合併到餐廳資訊
merged = pd.merge(
    restaurants,
    reviews_grouped,
    on="Restaurant_ID",
    how="left"  # 保留所有餐廳，即使沒有評論
)

# 儲存為新的 CSV
merged.to_csv("Kyoto_Restaurant_Info.csv", index=False, encoding="utf-8-sig")

print("✅ 已成功合併 Kyoto_Restaurant_Info.csv 與 Reviews.csv！")
