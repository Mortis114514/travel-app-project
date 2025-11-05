import pandas as pd

# 讀取資料
restaurants = pd.read_csv("data/Kyoto_Restaurant_Info.csv")
reviews = pd.read_csv("data/Reviews.csv")

# 確保欄位名稱一致
if "Restaurant_ID" not in restaurants.columns or "Restaurant_ID" not in reviews.columns:
    raise ValueError("❌ 餐廳或評論資料缺少 Restaurant_ID 欄位")

# 1️⃣ 計算每家餐廳的平均評論分數
avg_ratings = (
    reviews.groupby("Restaurant_ID")["Review_Rating"]
    .mean()
    .reset_index()
    .rename(columns={"Review_Rating": "Calculated_TotalRating"})
)

# 2️⃣ 合併平均分數回餐廳表
restaurants = pd.merge(
    restaurants,
    avg_ratings,
    on="Restaurant_ID",
    how="left"
)

# 3️⃣ 更新 TotalRating 欄位（若沒有評論就保留原本）
restaurants["TotalRating"] = restaurants["Calculated_TotalRating"].fillna(restaurants["TotalRating"])

# 移除暫時欄位
restaurants = restaurants.drop(columns=["Calculated_TotalRating"], errors="ignore")

# 存回檔案
restaurants.to_csv("data/Kyoto_Restaurant_Info.csv", index=False, encoding="utf-8-sig")

print("✅ 已根據評論重新計算每家餐廳的 TotalRating 並更新 CSV！")

# 分群邏輯
def categorize_rating(r):
    if r >= 4:
        return "4~5 星餐廳"
    elif r >= 3:
        return "3~3.9 星餐廳"
    elif r >= 2:
        return "2~2.9 星餐廳"
    else:
        return "低於 2 星"

restaurants["Rating_Category"] = restaurants["TotalRating"].apply(categorize_rating)

# 分群統計
category_counts = restaurants["Rating_Category"].value_counts()
print("⭐ 各評價區間餐廳數量：\n", category_counts)

# 儲存成新檔案
restaurants.to_csv("data/Kyoto_Restaurant_Info_Rated.csv", index=False, encoding="utf-8-sig")

print("✅ 已完成分群，結果存成 data/Kyoto_Restaurant_Info_Rated.csv")
