import dash
from dash import dcc, html, Input, Output, State, callback, MATCH
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# --- 1. 資料載入與整合 (Data Loading) ---
def load_and_prepare_data():
    """
    載入並整合所有資料：Hotels, Bookings, Reviews
    回傳一個包含所有分析所需欄位的 Master DataFrame
    """
    try:
        # 1. 讀取 CSV
        hotels = pd.read_csv('data/Hotels.csv')
        bookings = pd.read_csv('data/bookings.csv')
        reviews = pd.read_csv('data/HotelReviews.csv')
        
        # 統一欄位名稱
        if 'hotel_id' in bookings.columns:
            bookings.rename(columns={'hotel_id': 'Hotel_ID'}, inplace=True)
            
        # 確保 ID 格式一致
        for df in [hotels, bookings, reviews]:
            if 'Hotel_ID' in df.columns:
                df['Hotel_ID'] = pd.to_numeric(df['Hotel_ID'], errors='coerce')

        # 2. 準備 [市場分析資料] (Market Data)
        confirmed_bookings = bookings[bookings['status'] == 'Confirmed']
        price_stats = confirmed_bookings.groupby('Hotel_ID')['price_paid'].mean().reset_index(name='avg_price')
        
        cancel_stats = bookings.groupby('Hotel_ID')['status'].apply(
            lambda x: (x == 'Cancelled').sum() / len(x)
        ).reset_index(name='cancellation_rate')

        # 計算負評提及率
        def count_negative(text_series):
            keywords = ['dirty', 'noisy', 'poor', 'bad', 'terrible', '失望', '不佳', 'worst']
            count = 0
            for text in text_series:
                text = str(text).lower()
                if any(k in text for k in keywords):
                    count += 1
            return count

        review_aggs = reviews.groupby('Hotel_ID').agg({
            'Review_Rating': 'mean',
            'Review_ID': 'count',
            'Review_Text': count_negative
        }).reset_index()
        review_aggs.rename(columns={'Review_Rating': 'avg_rating', 'Review_ID': 'review_count', 'Review_Text': 'negative_mentions'}, inplace=True)
        review_aggs['negative_ratio'] = review_aggs['negative_mentions'] / review_aggs['review_count']

        # 合併資料
        market_df = pd.merge(hotels[['Hotel_ID', 'HotelName']], price_stats, on='Hotel_ID', how='inner')
        market_df = pd.merge(market_df, cancel_stats, on='Hotel_ID', how='left')
        market_df = pd.merge(market_df, review_aggs, on='Hotel_ID', how='left')
        
        # 填充空值
        market_df['avg_rating'] = market_df['avg_rating'].fillna(0).round(1)
        market_df['avg_price'] = market_df['avg_price'].fillna(0).round(0)
        market_df['negative_ratio'] = market_df['negative_ratio'].fillna(0)

        # 3. 準備 [詳細評論資料] (Reviews Data)
        reviews_full = pd.merge(reviews, hotels[['Hotel_ID', 'HotelName']], on='Hotel_ID', how='left')
        if 'Review_Date' in reviews_full.columns:
            reviews_full['Review_Date'] = pd.to_datetime(reviews_full['Review_Date'])

        return {
            'market_df': market_df,
            'reviews_df': reviews_full
        }

    except Exception as e:
        print(f"Error preparing analytics data: {e}")
        return {'market_df': pd.DataFrame(), 'reviews_df': pd.DataFrame()}

# --- 輔助函式：建立帶有說明的區塊 ---
def create_help_section(index_id, button_text, explanation_content):
    return html.Div([
        dbc.Button(
            [html.I(className="fas fa-info-circle", style={'marginRight': '8px'}), button_text],
            id={'type': 'help-btn', 'index': index_id},
            className="btn-outline-info",
            size="sm",
            n_clicks=0,
            style={'marginBottom': '10px', 'borderColor': '#003580', 'color': '#FFFFFF'}
        ),
        dbc.Collapse(
            dbc.Card(
                dbc.CardBody(explanation_content),
                style={'backgroundColor': '#FFFFFF', 'border': '1px solid #E8ECEF', 'color': '#4A5568', 'marginBottom': '15px'}
            ),
            id={'type': 'help-collapse', 'index': index_id},
            is_open=False,
        ),
    ])

# --- 2. 頁面佈局 (Layout) ---
def create_analytics_layout(data_dict):
    market_df = data_dict.get('market_df', pd.DataFrame())
    reviews_df = data_dict.get('reviews_df', pd.DataFrame())

    if market_df.empty:
        return html.Div("No data available. Please run generate_all_data.py first.", style={'color': 'red', 'padding': '2rem'})

    hotel_options = [{'label': h, 'value': h} for h in sorted(market_df['HotelName'].unique())]

    # --- 靜態圖表生成 ---
    # 1. CP 值矩陣
    fig_cp = px.scatter(
        market_df, x='avg_price', y='avg_rating', size='review_count', hover_name='HotelName',
        color='avg_rating', color_continuous_scale='RdYlGn', title='💎 Market Positioning (Price vs Rating)',
        labels={'avg_price': 'Avg Price', 'avg_rating': 'Rating'}
    )
    fig_cp.add_vline(x=market_df['avg_price'].mean(), line_dash="dash", line_color="grey")
    fig_cp.add_hline(y=market_df['avg_rating'].mean(), line_dash="dash", line_color="grey")
    fig_cp.update_layout(
        template='plotly_white', 
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='#FFFFFF',
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # 2. 負評關聯圖
    fig_neg = px.scatter(
        market_df, x='negative_ratio', y='cancellation_rate', hover_name='HotelName', size='review_count',
        color='cancellation_rate', color_continuous_scale='Reds', title='⚠️ Complaints vs Cancellations',
        labels={'negative_ratio': 'Negative Review %', 'cancellation_rate': 'Cancel Rate'}
    )
    fig_neg.update_layout(
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='#FFFFFF',
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # --- 解釋文案定義 ---
    help_cp = [
        html.H5("如何解讀這張圖？", style={'color': '#003580'}),
        html.Ul([
            html.Li("左上象限 (Low Price, High Rating)：高 CP 值的寶藏旅館。"),
            html.Li("右下象限 (High Price, Low Rating)：價格昂貴但評價低，需注意的地雷區。"),
            html.Li("點的大小：代表評論總數，越大的點代表越熱門。"),
            html.Li("虛線：市場平均價格與平均評分。")
        ])
    ]

    help_neg = [
        html.H5("負評是否導致退訂？", style={'color': '#ff6b6b'}),
        html.P("此圖分析「評論中提到髒亂(Dirty/Noisy)的比例」與「訂單取消率」的關係。"),
        html.Ul([
            html.Li("X軸：負評提及率 (越右邊代表越多人抱怨髒亂)。"),
            html.Li("Y軸：取消率 (越高代表越多人退訂)。"),
            html.Li("趨勢：如果點呈現向右上分佈，代表負評直接導致了高取消率。")
        ])
    ]

    help_dist = [
        html.H5("評分結構分析", style={'color': '#003580'}),
        html.P("顯示該飯店在 1~5 星的評價分佈情況。"),
        html.Ul([
            html.Li("健康的評分結構：應該是 4~5 星居多。"),
            html.Li("兩極化評價：如果 1 星和 5 星都很多，代表服務品質不穩定。")
        ])
    ]

    help_time = [
        html.H5("品質趨勢監控", style={'color': '#003580'}),
        html.P("顯示 30 天移動平均線 (Moving Average)，過濾掉單日波動。"),
        html.Ul([
            html.Li("上升趨勢：代表近期服務品質有改善。"),
            html.Li("下降趨勢：可能發生了特定事件導致滿意度下滑。"),
            html.Li("此圖可協助找出品質變化的具體時間點。")
        ])
    ]

    return html.Div([
        # Header
        html.Div([
            html.Button([html.I(className='fas fa-arrow-left'), ' Back'], id={'type': 'back-btn', 'index': 'analytics'}, className='btn-secondary'),
            html.H1("Analytics Dashboard", style={'color': '#003580', 'marginLeft': '2rem'})
        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '2rem', 'borderBottom': '1px solid #E8ECEF'}),

        # Section 1: Market Insights
        html.Div([
            html.H2("Market Insights", style={'color': '#1A1A1A', 'borderLeft': '4px solid #003580', 'paddingLeft': '10px'}),
            html.P("Compare all hotels to identify market opportunities and risks.", style={'color': '#888', 'marginBottom': '2rem'}),
            
            html.Div([
                # 圖表 1 區塊 (Market Positioning)
                html.Div([
                    create_help_section('cp-matrix', 'How to read CP Matrix', help_cp),
                    # --- 關鍵修正：加入 style={'height': '500px'} ---
                    dcc.Graph(figure=fig_cp, style={'height': '500px'})
                ], style={'flex': '1', 'minWidth': '500px', 'backgroundColor': '#FFFFFF', 'padding': '10px', 'borderRadius': '8px'}),

                # 圖表 2 區塊 (Negative Reviews)
                html.Div([
                    create_help_section('neg-scatter', 'Analysis Logic', help_neg),
                    # --- 關鍵修正：加入 style={'height': '500px'} ---
                    dcc.Graph(figure=fig_neg, style={'height': '500px'})
                ], style={'flex': '1', 'minWidth': '500px', 'backgroundColor': '#FFFFFF', 'padding': '10px', 'borderRadius': '8px'})
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '2rem'})
        ], style={'padding': '2rem', 'maxWidth': '1600px', 'margin': '0 auto'}),

        # Section 2: Specific Hotel Deep Dive
        html.Div([
            html.Hr(style={'borderColor': '#E8ECEF', 'margin': '3rem 0'}),
            html.H2("Hotel Deep Dive", style={'color': '#1A1A1A', 'borderLeft': '4px solid #003580', 'paddingLeft': '10px'}),
            html.P("Select a hotel to analyze its specific rating trends over time.", style={'color': '#888'}),

            # Controls
            html.Div([
                dcc.Dropdown(
                    id='analytics-hotel-dropdown',
                    options=hotel_options,
                    placeholder='Select a Hotel to Filter',
                    style={'flex': '1', 'maxWidth': '400px', 'color': '#000'}
                ),
                dcc.DatePickerRange(
                    id='analytics-date-picker',
                    min_date_allowed=reviews_df['Review_Date'].min(),
                    max_date_allowed=reviews_df['Review_Date'].max(),
                    start_date=reviews_df['Review_Date'].min(),
                    end_date=reviews_df['Review_Date'].max(),
                    style={'marginLeft': '20px', 'border': '1px solid #E8ECEF', 'borderRadius': '5px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'margin': '2rem 0'}),

            # Dynamic Charts Area
            html.Div([
                # 圖表 3 區塊 (Rating Distribution)
                html.Div([
                    create_help_section('dist-chart', 'What does this show?', help_dist),
                    # --- 關鍵修正：加入 style={'height': '500px'} ---
                    dcc.Graph(id='rating-distribution-chart', style={'height': '500px'})
                ], style={'flex': '1', 'minWidth': '500px', 'backgroundColor': '#FFFFFF', 'padding': '10px', 'borderRadius': '8px'}),

                # 圖表 4 區塊 (Rating Trend)
                html.Div([
                    create_help_section('time-chart', 'About Trend Line', help_time),
                    # --- 關鍵修正：加入 style={'height': '500px'} ---
                    dcc.Graph(id='rating-over-time-chart', style={'height': '500px'})
                ], style={'flex': '1', 'minWidth': '500px', 'backgroundColor': '#FFFFFF', 'padding': '10px', 'borderRadius': '8px'})
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '2rem'})

        ], style={'padding': '2rem', 'maxWidth': '1600px', 'margin': '0 auto', 'paddingBottom': '5rem'})

    ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh', 'overflowX': 'hidden'})

# --- 3. 註冊互動 Callbacks ---
def register_analytics_callbacks(app, data_dict):
    reviews_df = data_dict.get('reviews_df', pd.DataFrame())

    # --- 處理說明按鈕的開關 ---
    @app.callback(
        Output({'type': 'help-collapse', 'index': MATCH}, 'is_open'),
        [Input({'type': 'help-btn', 'index': MATCH}, 'n_clicks')],
        [State({'type': 'help-collapse', 'index': MATCH}, 'is_open')]
    )
    def toggle_help(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    # --- 原有的圖表互動 ---
    if reviews_df.empty:
        return

    @app.callback(
        [Output('rating-distribution-chart', 'figure'),
         Output('rating-over-time-chart', 'figure')],
        [Input('analytics-hotel-dropdown', 'value'),
         Input('analytics-date-picker', 'start_date'),
         Input('analytics-date-picker', 'end_date')]
    )
    def update_detail_charts(selected_hotel, start_date, end_date):
        filtered = reviews_df.copy()
        
        if start_date and end_date:
            filtered = filtered[(filtered['Review_Date'] >= start_date) & (filtered['Review_Date'] <= end_date)]
        
        title_suffix = "All Hotels"
        if selected_hotel:
            filtered = filtered[filtered['HotelName'] == selected_hotel]
            title_suffix = selected_hotel

        # 定義空圖表的樣式
        empty_fig_layout = dict(
            template='plotly_white', 
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='#FFFFFF',
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[dict(text="No Data Available", xref="paper", yref="paper", showarrow=False, font=dict(size=20))]
        )

        if filtered.empty:
            empty_fig = px.bar()
            empty_fig.update_layout(**empty_fig_layout)
            return empty_fig, empty_fig

        # 2. 製作分佈圖
        rating_counts = filtered['Review_Rating'].value_counts().sort_index()
        for i in range(1, 6):
            if i not in rating_counts: rating_counts[i] = 0
        rating_counts = rating_counts.sort_index()

        fig_dist = px.bar(
            x=rating_counts.index, y=rating_counts.values,
            labels={'x': 'Rating', 'y': 'Count'},
            title=f'Rating Distribution: {title_suffix}'
        )
        fig_dist.update_traces(marker_color='#003580')
        fig_dist.update_layout(template='plotly_white', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='#FFFFFF')

        # 3. 製作時間趨勢圖
        time_df = filtered.sort_values('Review_Date')
        time_df['rolling_avg'] = time_df['Review_Rating'].rolling(window=30, min_periods=1).mean()
        
        fig_time = px.line(
            time_df, x='Review_Date', y='rolling_avg',
            title=f'30-Day Rating Trend: {title_suffix}',
            labels={'rolling_avg': 'Avg Rating', 'Review_Date': 'Date'}
        )
        fig_time.update_traces(line_color='#003580', line_width=3)
        fig_time.update_yaxes(range=[0.5, 5.5])
        fig_time.update_layout(template='plotly_white', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='#FFFFFF')

        return fig_dist, fig_time