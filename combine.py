import csv

csv1_file = 'data/Kyoto_Restaurant_Info_Full.csv'  # 有 Price_Category 的 CSV
csv2_file = 'data/Kyoto_Restaurant_Info_Rated.csv'  # 有 Rating_Category 的 CSV
output_file = 'Combined_Restaurants.csv'

# 最終欄位順序
final_fields = [
    'Restaurant_ID', 'Name', 'JapaneseName', 'Station', 'FirstCategory', 'SecondCategory',
    'TotalRating', 'Lat', 'Long', 'DinnerPrice', 'LunchPrice', 'Price_Category',
    'DinnerRating', 'LunchRating', 'ReviewNum', 'Rating_Category'
]

def read_csv(file_path):
    with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

# 讀取兩個 CSV
csv1_rows = read_csv(csv1_file)
csv2_rows = read_csv(csv2_file)

# 合併資料並補齊缺失欄位
all_rows = []
for row in csv1_rows + csv2_rows:
    new_row = {field: row.get(field, '') for field in final_fields}
    all_rows.append(new_row)

# 重新編號 Restaurant_ID
for idx, row in enumerate(all_rows, start=1):
    row['Restaurant_ID'] = str(idx)

# 寫入新的 CSV
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=final_fields, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in all_rows:
        writer.writerow(row)

print(f"已成功合併兩個 CSV 並重新編號，共 {len(all_rows)} 筆資料")
