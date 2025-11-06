import csv

input_file = "data/Kyoto_Restaurant_Info_Full.csv"

# 輸出檔名
restaurant_file = "Restaurant.csv"
category_file = "Category.csv"
restaurant_category_file = "RestaurantCategory.csv"
price_file = "Price.csv"
rating_file = "Rating.csv"

# ====== Step 1：讀取原始 CSV ======
with open(input_file, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# ====== Step 2：準備拆表資料 ======

restaurant_rows = []
category_dict = {}         # 用來避免分類重複
restaurant_category_rows = []
price_rows = []
rating_rows = []

category_id_counter = 1

for row in rows:

    rid = row["Restaurant_ID"]

    # ✅ Restaurant Table
    restaurant_rows.append({
        "Restaurant_ID": rid,
        "Name": row["Name"],
        "JapaneseName": row["JapaneseName"],
        "Station": row["Station"],
        "Lat": row["Lat"],
        "Long": row["Long"]
    })

    # ✅ Category Table（自動去重）
    category_key = (row["FirstCategory"], row["SecondCategory"])
    if category_key not in category_dict:
        category_dict[category_key] = category_id_counter
        category_id_counter += 1

    category_id = category_dict[category_key]

    # ✅ RestaurantCategory（連接表）
    restaurant_category_rows.append({
        "Restaurant_ID": rid,
        "Category_ID": category_id
    })

    # ✅ Price Table
    price_rows.append({
        "Restaurant_ID": rid,
        "DinnerPrice": row["DinnerPrice"],
        "LunchPrice": row["LunchPrice"],
        "Price_Category": row["Price_Category"]
    })

    # ✅ Rating Table
    rating_rows.append({
        "Restaurant_ID": rid,
        "TotalRating": row["TotalRating"],
        "DinnerRating": row["DinnerRating"],
        "LunchRating": row["LunchRating"],
        "ReviewNum": row["ReviewNum"],
        "Rating_Category": row["Rating_Category"]
    })


# ====== Step 3：寫入拆後的 CSV（全欄位加雙引號） ======

def write_csv(filename, fieldnames, data):
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

# Restaurant
write_csv(
    restaurant_file,
    ["Restaurant_ID", "Name", "JapaneseName", "Station", "Lat", "Long"],
    restaurant_rows
)

# Category
write_csv(
    category_file,
    ["Category_ID", "FirstCategory", "SecondCategory"],
    [{"Category_ID": cid, "FirstCategory": key[0], "SecondCategory": key[1]}
     for key, cid in category_dict.items()]
)

# RestaurantCategory
write_csv(
    restaurant_category_file,
    ["Restaurant_ID", "Category_ID"],
    restaurant_category_rows
)

# Price
write_csv(
    price_file,
    ["Restaurant_ID", "DinnerPrice", "LunchPrice", "Price_Category"],
    price_rows
)

# Rating
write_csv(
    rating_file,
    ["Restaurant_ID", "TotalRating", "DinnerRating", "LunchRating", "ReviewNum", "Rating_Category"],
    rating_rows
)

print("✅ 拆表完成！已成功生成 5 個 CSV。")
