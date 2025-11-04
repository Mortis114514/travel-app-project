import pandas as pd

# 改這裡：加上 data/
restaurants = pd.read_csv("data/Kyoto_Restaurant_Info.csv")
reviews = pd.read_csv("data/Reviews.csv")

# 你的後續合併程式照舊
reviews_grouped = (
    reviews.groupby("Restaurant_ID")
    .agg({
        "Review_Text": lambda x: " | ".join(x),
        "Review_Rating": "mean"
    })
    .reset_index()
)

merged = pd.merge(
    restaurants,
    reviews_grouped,
    on="Restaurant_ID",
    how="left"
)

# 存回 data 資料夾
merged.to_csv("data/Kyoto_Restaurant_Info.csv", index=False, encoding="utf-8-sig")