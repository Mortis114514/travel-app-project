from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px

# ========== 讀取資料 ==========
restaurants = pd.read_csv("data/Kyoto_Restaurant_Info_Full.csv")
reviews = pd.read_csv("data/Reviews.csv")

# ========== 建立星等分類欄 ==========
def categorize_rating(r):
    if pd.isna(r):
        return None
    if r >= 4.0:
        return "4~5星"
    elif r >= 3.0:
        return "3~3.9星"
    elif r >= 2.0:
        return "2~2.9星"
    else:
        return "1~1.9星"

restaurants["Rating_Category"] = restaurants["TotalRating"].apply(categorize_rating)

# ========== 價格範圍說明 ==========
price_labels = {
    "平價": "平價（～¥2000）",
    "中價位": "中價位（¥2000～¥4999）",
    "高價位": "高價位（¥5000～¥9999）",
    "頂級": "頂級（¥10000+）"
}

# ========== Dash 應用程式 ==========
app = Dash(__name__)
app.title = "京都餐廳分析系統"

app.layout = html.Div([
    html.H2("🍣 京都餐廳星等與價位分析系統", 
            style={"textAlign": "center", "color": "#ffcccc"}),

    # ====== 篩選區 ======
    html.Div([
        html.Div([
            html.Label("選擇價位分類：", style={"color": "white"}),
            dcc.Dropdown(
                id="price-filter",
                options=[{"label": price_labels[c], "value": c} for c in price_labels],
                placeholder="請選擇價位分類",
                style={"width": "90%"}
            ),
        ], style={"display": "inline-block", "width": "45%", "verticalAlign": "top"}),

        html.Div([
            html.Label("選擇星等分類：", style={"color": "white"}),
            dcc.Dropdown(
                id="rating-filter",
                options=[{"label": c, "value": c} for c in sorted(restaurants["Rating_Category"].dropna().unique())],
                placeholder="請選擇星等分類",
                style={"width": "90%"}
            ),
        ], style={"display": "inline-block", "width": "45%", "verticalAlign": "top"})
    ], style={"marginBottom": "25px"}),

    # ====== 餐廳選擇 ======
    html.Div([
        html.Label("選擇餐廳：", style={"color": "white"}),
        dcc.Dropdown(id="restaurant-select", placeholder="請選擇餐廳", style={"width": "60%"}),
    ], style={"marginBottom": "20px"}),

    # ====== 星等長條圖 ======
    dcc.Graph(id="review-bar"),

    # ====== 評論清單 ======
    html.H4("📋 點選長條圖後顯示評論：", style={"color": "#ffcccc"}),
    html.Div(id="review-list", style={
        "whiteSpace": "pre-line",
        "padding": "10px",
        "border": "1px solid #555",
        "backgroundColor": "#222",
        "borderRadius": "10px",
        "color": "#fff"
    })
], style={
    "backgroundColor": "#111",
    "fontFamily": "微軟正黑體, sans-serif",
    "padding": "20px"
})

# ========== Callbacks ==========

# 1️⃣ 根據「價位」與「星等」篩選餐廳清單
@app.callback(
    Output("restaurant-select", "options"),
    Input("price-filter", "value"),
    Input("rating-filter", "value")
)
def update_restaurant_list(selected_price, selected_rating):
    filtered = restaurants.copy()

    if selected_price:
        filtered = filtered[filtered["Price_Category"] == selected_price]
    if selected_rating:
        filtered = filtered[filtered["Rating_Category"] == selected_rating]

    if filtered.empty:
        return []

    return [{"label": row["Name"], "value": row["Restaurant_ID"]} for _, row in filtered.iterrows()]


# 2️⃣ 根據餐廳顯示評論星等長條圖
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

    restaurant_name = restaurants.loc[
        restaurants["Restaurant_ID"] == restaurant_id, "Name"
    ].values[0]

    fig = px.histogram(
        restaurant_reviews,
        x="Review_Rating",
        nbins=5,
        title=f"🍣 {restaurant_name} 的評論星等分佈",
        labels={"Review_Rating": "星等", "count": "評論數量"}
    )
    fig.update_layout(
        bargap=0.2,
        xaxis=dict(dtick=1),
        title_x=0.5,
        plot_bgcolor="#222",
        paper_bgcolor="#111",
        font=dict(color="#fff")
    )
    return fig


# 3️⃣ 點擊長條圖 → 顯示該星等評論
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

    selected_rating = int(clickData["points"][0]["x"])
    restaurant_reviews = reviews[
        (reviews["Restaurant_ID"] == restaurant_id) &
        (reviews["Review_Rating"] == selected_rating)
    ]

    if restaurant_reviews.empty:
        return f"⭐ 沒有 {selected_rating} 星的評論"

    review_texts = restaurant_reviews["Review_Text"].tolist()
    review_display = "\n\n".join([f"⭐ {selected_rating} 星評論：{t}" for t in review_texts])
    return review_display


# ========== 啟動 ==========
if __name__ == "__main__":
    app.run(debug=True)
