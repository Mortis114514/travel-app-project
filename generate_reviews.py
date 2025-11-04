import pandas as pd
import random
import csv

# 讀取餐廳資料
df_restaurants = pd.read_csv('data/Kyoto_Restaurant_Info.csv')

# 評論模板（中英日混合，更多樣性）
review_templates_5star = [
    # 5星評論 - 英文
    "Absolutely phenomenal! One of the best meals I've ever had.",
    "Outstanding in every way. The attention to detail is remarkable.",
    "Perfection! From the food to the service, everything was flawless.",
    "This place deserves all the praise. Simply exceptional!",
    "Mind-blowing experience! Will definitely come back.",
    "Best restaurant in Kyoto, hands down!",
    "The chef is a true artist. Every dish was a masterpiece.",
    "Incredible atmosphere and world-class cuisine.",
    "Beyond expectations! Worth every penny.",
    "Five stars aren't enough for this place!",

    # 5星評論 - 中文
    "完美的用餐體驗！每一道菜都令人驚艷。",
    "超越期待！這是我在京都吃過最好的餐廳。",
    "無可挑剔！服務、環境、食物都是一流水準。",
    "太棒了！強烈推薦給所有來京都的朋友。",
    "京都第一名餐廳！必須二訪三訪。",
    "料理精緻美味，服務貼心周到，值得五顆星！",
    "完全超出預期，CP值爆表！",
    "從裝潢到料理都無懈可擊，讚不絕口。",

    # 5星評論 - 日文
    "最高の体験でした！また絶対に来ます。",
    "完璧な料理と素晴らしいサービス。京都で一番好きなお店です。",
    "言葉にできないほど美味しかった！感動しました。",
    "期待以上でした。全ての料理が絶品です。",
    "京都に来たら必ず訪れるべきお店。強くおすすめします！",
    "雰囲気も味も最高！特別な日にぴったりです。",
    "素晴らしい！職人の技術が光る一品一品。",
]

review_templates_4star = [
    # 4星評論 - 英文
    "Excellent food and friendly staff. Highly recommend!",
    "Great dining experience, will definitely return.",
    "Very good! Just a few minor details could be improved.",
    "Impressive quality and presentation.",
    "Really enjoyed our meal here. Solid choice!",
    "Wonderful atmosphere and delicious dishes.",
    "The food was fantastic, service was prompt.",
    "Beautiful presentation and authentic flavors.",
    "Great value for money, portions were generous.",
    "Lovely place with a cozy ambiance.",

    # 4星評論 - 中文
    "很棒的餐廳！食物美味，環境舒適。",
    "料理精緻好吃，服務態度親切，值得推薦。",
    "整體表現優秀，會想再來光顧。",
    "品質很好，價格合理，CP值高。",
    "環境優雅，適合朋友聚餐或約會。",
    "食材新鮮，口味道地，很滿意。",
    "服務人員很專業，料理水準穩定。",
    "氣氛很棒，料理也很有特色。",

    # 4星評論 - 日文
    "とても美味しかったです。また来たいと思います。",
    "料理のクオリティが高く、満足しました。",
    "雰囲気が良くて、料理も美味しい。おすすめです。",
    "サービスも丁寧で、居心地が良かったです。",
    "値段に見合った素晴らしい料理でした。",
    "新鮮な食材を使った本格的な味。",
]

review_templates_3star = [
    # 3星評論 - 英文
    "It was okay. Nothing particularly memorable.",
    "Average experience, food was decent but not exceptional.",
    "Service was a bit slow, but food was acceptable.",
    "Not bad, but there are better options in the area.",
    "Decent place for a quick meal.",
    "The food was alright, reasonably priced.",
    "Middle of the road. Nothing to complain about.",
    "Fair quality, might come back if in the area.",

    # 3星評論 - 中文
    "普通的餐廳，沒有特別驚艷。",
    "食物水準中等，價格還算可以。",
    "環境還不錯，但料理表現普通。",
    "可以試試看，但不會特別推薦。",
    "份量適中，口味中規中矩。",
    "服務還可以，食物表現平平。",
    "沒有太大驚喜，也沒什麼缺點。",

    # 3星評論 - 日文
    "普通でした。特に印象に残るものはありませんでした。",
    "まあまあですね。期待していたほどではなかった。",
    "味は悪くないけど、特別おすすめするほどでもない。",
    "可もなく不可もなく。値段相応かな。",
    "普通の居酒屋。次はないかも。",
]

review_templates_2star = [
    # 2星評論 - 英文
    "Disappointing. Expected much better.",
    "Service was poor and food was mediocre.",
    "Overpriced for what you get.",
    "Not worth the hype. Quality was below average.",
    "Had better meals elsewhere for less money.",
    "Food arrived cold, service was inattentive.",
    "The portions were tiny for the price.",

    # 2星評論 - 中文
    "有點失望，CP值不高。",
    "服務態度需要改進，等待時間太長。",
    "料理品質不如預期，價格偏貴。",
    "環境吵雜，用餐體驗不太好。",
    "份量很少，口味也很普通。",
    "期待落空，可能不會再來了。",

    # 2星評論 - 日文
    "期待外れでした。値段が高すぎる。",
    "サービスが悪く、料理も期待以下。",
    "コストパフォーマンスが悪い。",
    "もう二度と来ないと思います。",
]

review_templates_1star = [
    # 1星評論 - 英文
    "Terrible experience. Would not recommend at all.",
    "Worst meal I've had in Kyoto. Avoid!",
    "Completely disappointed. Food was bad and service worse.",
    "Save your money and go somewhere else.",
    "Awful in every aspect. Total waste of time and money.",

    # 1星評論 - 中文
    "非常不推薦，用餐體驗很糟糕。",
    "完全不值得，浪費錢和時間。",
    "服務態度惡劣，食物也很難吃。",
    "這是我在京都吃過最差的餐廳。",
    "千萬不要來，完全踩雷。",

    # 1星評論 - 日文
    "最悪でした。絶対におすすめしません。",
    "二度と行きません。お金の無駄です。",
    "ひどい料理とサービス。星一つもあげたくない。",
    "京都で一番まずい店。避けるべき。",
]

# 具體料理類型評論（隨機穿插使用）
specific_dish_reviews = [
    # 英文
    "The sushi was incredibly fresh and melted in my mouth!",
    "Best ramen I've had in Japan. The broth was perfect.",
    "The tempura was crispy and not oily at all.",
    "Amazing wagyu beef, cooked to perfection.",
    "The kaiseki course was a work of art.",
    "Great sake selection, staff helped us choose perfectly.",
    "The matcha dessert was heavenly!",
    "Yakitori was grilled perfectly with great seasoning.",
    "The okonomiyaki was authentic and delicious.",
    "Tonkatsu was crispy outside, juicy inside.",

    # 中文
    "壽司超級新鮮，入口即化！",
    "拉麵湯頭濃郁，是我喝過最好喝的。",
    "天婦羅炸得剛剛好，完全不油膩。",
    "和牛品質極佳，口感軟嫩多汁。",
    "懷石料理每一道都很精緻，視覺與味覺的雙重享受。",
    "清酒種類豐富，侍酒師推薦得很專業。",
    "抹茶甜點超級好吃，不會太甜。",
    "串燒烤得恰到好處，調味完美。",
    "大阪燒很道地，料很多很實在。",
    "豬排外酥內嫩，醬汁也很搭。",

    # 日文
    "お寿司が新鮮で、口の中でとろけました！",
    "ラーメンのスープが絶品。今まで食べた中で一番美味しい。",
    "天ぷらがサクサクで、油っぽくない。",
    "和牛のクオリティが素晴らしい。柔らかくてジューシー。",
    "懐石料理の一品一品が芸術品のよう。",
    "日本酒の種類が豊富で、ソムリエの説明も丁寧。",
    "抹茶デザートが絶品！甘さ控えめで完璧。",
    "焼き鳥が絶妙な焼き加減。味付けも最高。",
    "お好み焼きが本格的で、具材もたっぷり。",
    "とんかつが外はサクサク、中はジューシー。",
]

# 根據評分選擇合適的評論
def get_review_by_rating(rating):
    # 80% 使用對應星級的評論，20% 使用具體料理評論
    use_specific = random.random() < 0.2

    if use_specific:
        return random.choice(specific_dish_reviews)

    if rating == 5:
        return random.choice(review_templates_5star)
    elif rating == 4:
        return random.choice(review_templates_4star)
    elif rating == 3:
        return random.choice(review_templates_3star)
    elif rating == 2:
        return random.choice(review_templates_2star)
    else:  # rating == 1
        return random.choice(review_templates_1star)

# 生成評論資料
reviews = []
review_id = 1

for _, restaurant in df_restaurants.iterrows():
    restaurant_id = restaurant.iloc[0]  # 第一個欄位是 restaurant ID

    # 為每個餐廳生成 30 則評論
    for _ in range(30):
        # 生成評分（1-5星），參考餐廳的 TotalRating 來產生更真實的分布
        # 大部分餐廳會集中在某些星級，而不是平均分布
        total_rating = restaurant['TotalRating']

        if pd.notna(total_rating):
            # 根據餐廳的總評分產生更真實的評論評分分布
            if total_rating >= 3.7:
                # 高評分餐廳：主要是 4-5 星，偶爾有 3 星
                rating = random.choices([3, 4, 5], weights=[5, 35, 60])[0]
            elif total_rating >= 3.4:
                # 中高評分餐廳：4 星為主，5 星和 3 星各占一些
                rating = random.choices([3, 4, 5], weights=[15, 55, 30])[0]
            elif total_rating >= 3.0:
                # 中等評分餐廳：3-4 星為主
                rating = random.choices([2, 3, 4, 5], weights=[5, 45, 40, 10])[0]
            elif total_rating >= 2.5:
                # 中低評分餐廳：2-3 星為主
                rating = random.choices([1, 2, 3, 4], weights=[5, 50, 35, 10])[0]
            else:
                # 低評分餐廳：1-2 星為主
                rating = random.choices([1, 2, 3], weights=[40, 50, 10])[0]
        else:
            # 如果沒有總評分，偏向中等偏上評分（符合大部分餐廳情況）
            rating = random.choices([1, 2, 3, 4, 5], weights=[3, 10, 25, 42, 20])[0]

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
