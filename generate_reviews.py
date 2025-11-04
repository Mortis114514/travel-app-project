import pandas as pd
import random
import csv

# 讀取餐廳資料
df_restaurants = pd.read_csv('data/Kyoto_Restaurant_Info.csv')

# 評論模板（中英文混合，符合旅遊 app 的使用情境）
review_templates = [
    # 正面評論 (4-5星)
    "Amazing food and great atmosphere! Highly recommended.",
    "The staff was very friendly and the food was delicious.",
    "One of the best dining experiences in Kyoto!",
    "Excellent service and authentic Japanese cuisine.",
    "Beautiful presentation and wonderful flavors.",
    "超棒的用餐體驗！食物很美味，服務態度也很好。",
    "環境舒適，料理精緻，值得再訪。",
    "京都必訪餐廳之一，品質很穩定。",
    "服務人員很親切，料理口味道地。",
    "氣氛很棒，適合朋友聚餐或慶祝。",
    "Food quality exceeded expectations. Will definitely return!",
    "Perfect spot for a special occasion.",
    "The chef's special was outstanding!",
    "Great value for money and generous portions.",
    "Loved the traditional Japanese ambiance.",

    # 中等評論 (3星)
    "The food was okay, nothing special but decent.",
    "Average experience, might try again.",
    "Service was a bit slow but food was good.",
    "Decent place, reasonably priced.",
    "Not bad, but there are better options nearby.",
    "普通的餐廳，價格還算合理。",
    "食物水準中等，服務還可以。",
    "環境不錯但料理表現普通。",
    "可以嘗試看看，但不會特別推薦。",
    "份量適中，口味還算不錯。",

    # 較負面評論 (1-2星)
    "Disappointed with the quality for the price.",
    "Service needs improvement, food was cold.",
    "Expected better based on the reviews.",
    "Overpriced and underwhelming.",
    "Would not recommend, poor experience overall.",
    "服務態度需要加強，等待時間太長。",
    "CP值不高，料理品質不如預期。",
    "環境吵雜，用餐體驗不佳。",
    "價格偏貴但份量太少。",
    "不會再來第二次。",

    # 具體評論
    "The sushi was incredibly fresh!",
    "Best ramen I've had in Kyoto.",
    "The tempura was perfectly crispy.",
    "Great sake selection.",
    "Loved the seasonal menu items.",
    "壽司超級新鮮，推薦給喜歡生魚片的朋友。",
    "拉麵湯頭濃郁，麵條彈牙。",
    "天婦羅炸得很酥脆，不會太油膩。",
    "清酒種類豐富，店員會幫忙推薦。",
    "季節限定菜單很有特色。",
    "The wagyu beef melted in my mouth.",
    "Cozy izakaya with great small plates.",
    "Authentic kaiseki experience.",
    "The matcha dessert was divine.",
    "Hidden gem, glad we found this place!",
]

# 根據評分選擇合適的評論
def get_review_by_rating(rating):
    if rating >= 4:
        # 4-5星：選擇正面評論
        return random.choice(review_templates[0:25])
    elif rating == 3:
        # 3星：選擇中等評論
        return random.choice(review_templates[25:35])
    else:
        # 1-2星：選擇較負面評論
        return random.choice(review_templates[35:45] + review_templates[45:])

# 生成評論資料
reviews = []
review_id = 1

for _, restaurant in df_restaurants.iterrows():
    restaurant_id = restaurant.iloc[0]  # 第一個欄位是 restaurant ID

    # 為每個餐廳生成 30 則評論
    for _ in range(30):
        # 生成評分（1-5星），參考餐廳的 TotalRating 來產生合理的分布
        total_rating = restaurant['TotalRating']

        if pd.notna(total_rating):
            # 根據餐廳的總評分產生類似分布的評論評分
            if total_rating >= 3.5:
                rating = random.choices([3, 4, 5], weights=[10, 40, 50])[0]
            elif total_rating >= 3.0:
                rating = random.choices([2, 3, 4, 5], weights=[10, 40, 40, 10])[0]
            else:
                rating = random.choices([1, 2, 3, 4], weights=[20, 40, 30, 10])[0]
        else:
            # 如果沒有總評分，隨機生成
            rating = random.choices([1, 2, 3, 4, 5], weights=[5, 15, 30, 35, 15])[0]

        # 根據評分選擇評論文字
        review_text = get_review_by_rating(rating)

        reviews.append({
            'Review_ID': review_id,
            'Restaurant_ID': restaurant_id,
            'Review_Text': review_text,
            'Review_Rating': rating
        })

        review_id += 1

# 建立 DataFrame
df_reviews = pd.DataFrame(reviews)

# 儲存為 CSV
df_reviews.to_csv('data/Reviews.csv', index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

print(f"Successfully generated {len(reviews)} reviews")
print(f"Number of restaurants: {len(df_restaurants)}")
print(f"Average reviews per restaurant: {len(reviews) / len(df_restaurants):.0f}")
print(f"File saved to: data/Reviews.csv")
