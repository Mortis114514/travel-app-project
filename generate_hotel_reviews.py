import pandas as pd
import random
import csv

# Read hotels data
try:
    df_hotels = pd.read_csv('data/Hotels.csv')
except Exception as e:
    print('Error reading Hotels.csv:', e)
    raise


# Phrase pools to create more varied comments
openings = [
    "The stay was", "I found the hotel", "Overall it was", "We had a", "My experience was"
]

aspects = [
    "room", "service", "location", "breakfast", "cleanliness", "staff", "value"
]

adjectives_positive = [
    "excellent", "fantastic", "very good", "pleasant", "comfortable", "impressive"
]

adjectives_neutral = ["okay", "average", "fine", "acceptable"]
adjectives_negative = ["disappointing", "poor", "below expectations", "terrible"]

endings = [
    ". Would stay again.",
    ". Recommended for the price.",
    ". Friendly staff and clean rooms.",
    ". A convenient choice for travelers.",
    ". Not much to complain about."
]

specific_reviews = [
    "Great breakfast selection.",
    "The bed was very comfortable.",
    "Amazing view from the room.",
    "Close to public transport and attractions.",
    "早餐豐富且美味。",
    "部屋からの眺めが最高でした。",
    "The housekeeping was quick and thorough.",
    "Helpful front desk service during check-in."
]


def compose_comment(rating):
    """Compose a comment from phrase pools based on rating to maximize variation."""
    # Occasionally return a specific short review
    if random.random() < 0.15:
        return random.choice(specific_reviews)

    opener = random.choice(openings)
    aspect = random.choice(aspects)

    if rating >= 4:
        adj = random.choice(adjectives_positive)
        end = random.choice(endings)
        core = f"{opener} {adj} regarding the {aspect}"
    elif rating == 3:
        adj = random.choice(adjectives_neutral)
        end = random.choice([".", random.choice(endings)])
        core = f"{opener} {adj} for the {aspect}"
    else:
        adj = random.choice(adjectives_negative)
        end = random.choice([".", ". Would not recommend."])
        core = f"{opener} {adj} about the {aspect}"

    # Add a small random detail to increase uniqueness
    details = [
        "The staff were attentive.",
        "Check-in was smooth.",
        "Room had a nice view.",
        "Noise was minimal at night.",
        "Bathroom was clean and well stocked.",
        "Location is central and practical."
    ]

    if random.random() < 0.35:
        detail = " " + random.choice(details)
    else:
        detail = ""

    return (core + end + detail).strip()


def compose_comment_en(rating):
    # English composition
    if random.random() < 0.12:
        return random.choice(specific_reviews)

    opener = random.choice(openings)
    aspect = random.choice(aspects)

    if rating >= 4:
        adj = random.choice(adjectives_positive)
        end = random.choice(endings)
        core = f"{opener} {adj} regarding the {aspect}"
    elif rating == 3:
        adj = random.choice(adjectives_neutral)
        end = random.choice([".", random.choice(endings)])
        core = f"{opener} {adj} for the {aspect}"
    else:
        adj = random.choice(adjectives_negative)
        end = random.choice([".", ". Would not recommend."])
        core = f"{opener} {adj} about the {aspect}"

    details = [
        "The staff were attentive.",
        "Check-in was smooth.",
        "Room had a nice view.",
        "Noise was minimal at night.",
        "Bathroom was clean and well stocked.",
        "Location is central and practical."
    ]

    detail = (" " + random.choice(details)) if random.random() < 0.35 else ""
    end = end if 'end' in locals() else "."
    return (core + end + detail).strip()


# 中文片語庫與組合
cn_openings = ["住宿體驗", "整體來說", "這次入住", "感覺是", "個人覺得"]
cn_aspects = ["房間", "服務", "地點", "早餐", "整潔度", "員工", "性價比"]
cn_pos = ["很棒", "不錯", "舒適", "令人滿意"]
cn_neu = ["一般", "還可以", "普通"]
cn_neg = ["失望", "不佳", "需要改進"]
cn_endings = ["，會再入住。", "，值得推薦。", "，對旅客來說方便。", "，沒有太大缺點。"]
cn_details = ["入住手續快速。", "地點交通方便。", "房間乾淨。", "服務人員態度很好。"]

def compose_comment_cn(rating):
    if random.random() < 0.12:
        return random.choice(specific_reviews)
    opener = random.choice(cn_openings)
    aspect = random.choice(cn_aspects)
    if rating >= 4:
        adj = random.choice(cn_pos)
        end = random.choice(cn_endings)
    elif rating == 3:
        adj = random.choice(cn_neu)
        end = random.choice(["。", random.choice(cn_endings)])
    else:
        adj = random.choice(cn_neg)
        end = random.choice(["。", "，不推薦。"])

    detail = ("" if random.random() > 0.4 else random.choice(cn_details))
    return f"{opener}{adj}，關於{aspect}{end}{detail}".strip()


# 日文片語庫與組合
jp_openings = ["滞在は", "全体的に", "今回の宿泊は", "個人的には", "感想としては"]
jp_aspects = ["部屋", "サービス", "立地", "朝食", "清潔さ", "スタッフ", "コスパ"]
jp_pos = ["素晴らしい", "快適", "満足しました", "良い"]
jp_neu = ["普通", "まあまあ", "可もなく不可もなく"]
jp_neg = ["期待外れ", "不満", "改善が必要"]
jp_endings = ["。また泊まりたいです。", "。おすすめします。", "。旅行者に便利です。"]
jp_details = ["チェックインがスムーズでした。", "場所が便利でした。", "部屋は清潔でした。", "スタッフが親切でした。"]

def compose_comment_jp(rating):
    if random.random() < 0.12:
        return random.choice(specific_reviews)
    opener = random.choice(jp_openings)
    aspect = random.choice(jp_aspects)
    if rating >= 4:
        adj = random.choice(jp_pos)
        end = random.choice(jp_endings)
    elif rating == 3:
        adj = random.choice(jp_neu)
        end = random.choice(["。", random.choice(jp_endings)])
    else:
        adj = random.choice(jp_neg)
        end = random.choice(["。", "。おすすめしません。"])

    detail = ("" if random.random() > 0.4 else random.choice(jp_details))
    return f"{opener}{adj}、{aspect}について{end}{detail}".strip()


def get_text_by_rating(rating):
    # Decide language: English 60%, Chinese 25%, Japanese 15%
    r = random.random()
    if r < 0.6:
        return compose_comment_en(rating)
    elif r < 0.85:
        return compose_comment_cn(rating)
    else:
        return compose_comment_jp(rating)

reviews = []
review_id = 1

for _, hotel in df_hotels.iterrows():
    try:
        hotel_id = hotel['Hotel_ID']
    except Exception:
        # fallback to first column
        hotel_id = hotel.iloc[0]

    # generate a variable number of reviews per hotel (e.g., 10-40)
    n_reviews = random.randint(10, 40)
    hotel_rating = None
    try:
        hotel_rating = float(hotel.get('Rating', float('nan')))
    except Exception:
        hotel_rating = float('nan')

    for _ in range(n_reviews):
        # generate rating biased by hotel's average rating when available
        if pd.notna(hotel_rating):
            if hotel_rating >= 4.0:
                rating = random.choices([4,5,3], weights=[35,55,10])[0]
            elif hotel_rating >= 3.5:
                rating = random.choices([3,4,5], weights=[20,55,25])[0]
            elif hotel_rating >= 3.0:
                rating = random.choices([2,3,4], weights=[10,55,35])[0]
            else:
                rating = random.choices([1,2,3], weights=[40,50,10])[0]
        else:
            rating = random.choices([1,2,3,4,5], weights=[3,10,25,42,20])[0]

        text = get_text_by_rating(rating)

        reviews.append({
            'Review_ID': review_id,
            'Hotel_ID': hotel_id,
            'Review_Text': text,
            'Review_Rating': rating
        })
        review_id += 1

# Save as CSV
df_reviews = pd.DataFrame(reviews)
output_path = 'data/HotelReviews.csv'
if not df_reviews.empty:
    df_reviews.to_csv(output_path, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    print(f"Saved {len(df_reviews)} generated hotel reviews to {output_path}")
else:
    print('No reviews generated')
