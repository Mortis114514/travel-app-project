from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px

# ========== 資料讀取 ==========
restaurants = pd.read_csv("data/Kyoto_Restaurant_Info.csv")
reviews = pd.read_csv("data/Reviews.csv")
rated = pd.read_csv("data/Kyoto_Restaurant_Info_Rated.csv")

# 合併星等分類資訊（確保包含所有星等）
restaurants = pd.merge(
    restaurants,
    rated[["Restaurant_ID", "TotalRating", "Rating_Category"]],
    on="Restaurant_ID",
    how="left"
)

# ========== Dash App ==========
app = Dash(__name__)
app.title = "京都餐廳星等分析系統"

app.layout = html.Div([
    html.H2("🍣 京都餐廳星等分析系統", style={"textAlign": "center"}),

    html.Div([
        html.Label("選擇星等分類："),
        dcc.Dropdown(
            id="rating-filter",
            options=[{"label": c, "value": c} for c in sorted(restaurants["Rating_Category"].dropna().unique())],
            placeholder="選擇星等分類",
            style={"width": "60%"}
        ),
    ], style={"marginBottom": "20px"}),

    html.Div([
        html.Label("選擇餐廳："),
        dcc.Dropdown(id="restaurant-select", placeholder="選擇餐廳", style={"width": "60%"}),
    ], style={"marginBottom": "20px"}),

    html.Div([
        dcc.Graph(id="review-bar"),
    ]),

    html.H4("📋 點選長條圖後顯示評論："),
    html.Div(id="review-list", style={"whiteSpace": "pre-line", "padding": "10px", "border": "1px solid #ccc"})
])

# ========== Callbacks ==========

# 1️⃣ 根據星等分類篩選餐廳
@app.callback(
    Output("restaurant-select", "options"),
    Input("rating-filter", "value")
)
def update_restaurant_list(selected_category):
    if not selected_category:
        return []
    filtered = restaurants[restaurants["Rating_Category"] == selected_category]
    return [{"label": row["Name"], "value": row["Restaurant_ID"]} for _, row in filtered.iterrows()]


# 2️⃣ 根據餐廳 ID 顯示評論星等長條圖
@app.callback(
    Output("review-bar", "figure"),
    Input("restaurant-select", "value")
)
def update_review_chart(restaurant_id):
    if not restaurant_id:
        return px.bar(title="請選擇餐廳")

    restaurant_reviews = reviews[reviews["Restaurant_ID"] == restaurant_id]
    if restaurant_reviews.empty:
        return px.bar(title="此餐廳暫無評論")

    # 根據 ID 找出餐廳名稱
    restaurant_name = restaurants.loc[
        restaurants["Restaurant_ID"] == restaurant_id, "Name"
    ].values[0]

    # 用 histogram 顯示每個星等評論數
    fig = px.histogram(
        restaurant_reviews,
        x="Review_Rating",
        nbins=5,
        title=f"🍣 {restaurant_name} 的評論星等分佈",
        labels={"Review_Rating": "星等", "count": "評論數量"}
    )
    fig.update_layout(bargap=0.2)
    return fig


# 3️⃣ 點擊長條圖 → 顯示該星等評論文字
@app.callback(
    Output("review-list", "children"),
    Input("review-bar", "clickData"),
    Input("restaurant-select", "value")
)
def display_selected_reviews(clickData, restaurant_id):
    if not restaurant_id:
        return "請先選擇餐廳"
    if not clickData:
        return "點擊上方長條圖中的星等柱，查看對應的評論"

    # 從點擊事件中取出星等值
    selected_rating = int(clickData["points"][0]["x"])
    restaurant_reviews = reviews[
        (reviews["Restaurant_ID"] == restaurant_id) &
        (reviews["Review_Rating"] == selected_rating)
    ]

    if restaurant_reviews.empty:
        return f"⭐ 沒有 {selected_rating} 星的評論"

    # 取出評論文字
    review_texts = restaurant_reviews["Review_Text"].tolist()
    review_display = "\n\n".join([f"⭐ {selected_rating}星評論：{t}" for t in review_texts])
    return review_display


# ========== 啟動 ==========
if __name__ == "__main__":
    app.run(debug=True)
