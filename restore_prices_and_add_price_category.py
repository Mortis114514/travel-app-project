import pandas as pd
import re

# # ====== 讀取原始與修改後的餐廳資料 ======
# original = pd.read_csv("data/Kyoto_Restaurant_Info.csv")           # 原始完整檔案（含價格區間）
# modified = pd.read_csv("data/Kyoto_Restaurant_Info_Rated.csv")     # 修改後（無價格欄）

# # ====== 從原始資料提取價格欄 ======
# price_cols = [col for col in ["Name", "DinnerPrice", "LunchPrice"] if col in original.columns]
# price_df = original[price_cols]

# # 合併價格資料（以餐廳名稱對應）
# merged_df = pd.merge(modified, price_df, on="Name", how="left")

# ====== 定義：將價格文字轉為平均數值（僅用於分類用，不改動原文字） ======

merged_df = pd.read_csv("data/Kyoto_Restaurant_Info_Rated.csv")

def extract_avg_price(value):
    if pd.isna(value):
        return None
    if not isinstance(value, str):
        return value

    # 移除符號
    text = value.replace("円", "").replace("￥", "").replace(",", "").strip()
    # 擷取數字
    numbers = re.findall(r"\d+", text)
    if len(numbers) == 0:
        return None
    elif len(numbers) == 1:
        return float(numbers[0])
    else:
        return (float(numbers[0]) + float(numbers[1])) / 2

# 建立暫時欄位供分類用
merged_df["DinnerPrice_num"] = merged_df["DinnerPrice"].apply(extract_avg_price)
merged_df["LunchPrice_num"] = merged_df["LunchPrice"].apply(extract_avg_price)

# ====== 計算平均價格 ======
merged_df["AvgPrice_num"] = merged_df[["DinnerPrice_num", "LunchPrice_num"]].mean(axis=1, skipna=True)

# ====== 依據平均價格劃分價位分類 ======
def categorize_price(price):
    if pd.isna(price):
        return "未知"
    elif price < 2000:
        return "平價"
    elif price < 5000:
        return "中價位"
    elif price < 10000:
        return "高價位"
    else:
        return "頂級"

merged_df["Price_Category"] = merged_df["AvgPrice_num"].apply(categorize_price)

# ====== 輸出前移除暫時數值欄位 ======
merged = merged_df.drop(columns=["DinnerPrice_num", "LunchPrice_num", "AvgPrice_num"])

# ====== 重新排序欄位 ======
ordered_cols = [
    "Restaurant_ID", "Name", "JapaneseName", "Station",
    "FirstCategory", "SecondCategory", "TotalRating",
    "Lat", "Long", "DinnerPrice", "LunchPrice", "Price_Category"
]
merged = merged[ordered_cols]

# ====== 輸出成新 CSV ======
output_path = "data/Kyoto_Restaurant_Info_Full.csv"
merged.to_csv(output_path, index=False, encoding="utf-8-sig")

print("✅ 已根據價格區間分類並保留原文字格式！")
print(f"📄 輸出檔案：{output_path}")
print(f"🔹 共 {len(merged)} 筆餐廳資料")
