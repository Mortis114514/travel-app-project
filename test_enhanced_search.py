"""
Enhanced Search System - Test Application
增強搜尋系統測試程式

此程式用於測試增強搜尋功能，獨立於主應用程式運行
"""

from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime

# 導入增強搜尋組件
from components.enhanced_search import (
    create_enhanced_search_bar,
    create_search_stores,
    generate_search_suggestions,
    create_suggestion_item,
    create_filter_chip,
    create_history_item,
    create_popular_item
)

# 載入餐廳資料
restaurants_df = pd.read_csv('./data/Kyoto_Restaurant_Info_Full.csv')

# 初始化應用
app = Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    '/assets/voyage_styles.css',
    '/assets/enhanced_search_styles.css'
],
           title='Enhanced Search Test',
           suppress_callback_exceptions=True)

# 應用布局
app.layout = html.Div([
    html.Div([
        html.H1('Enhanced Search System Test', style={
            'textAlign': 'center',
            'color': '#deb522',
            'marginBottom': '2rem',
            'fontSize': '2.5rem'
        }),

        html.P('測試增強搜尋功能的獨立應用程式', style={
            'textAlign': 'center',
            'color': '#888',
            'marginBottom': '3rem'
        }),

        # 搜尋系統組件
        create_enhanced_search_bar(restaurants_df),

        # 搜尋 Stores
        create_search_stores(),

        # 搜尋結果顯示區域
        html.Div([
            html.H3('Search Results', style={
                'color': '#ffffff',
                'marginTop': '3rem',
                'marginBottom': '1rem'
            }),
            html.Div(id='test-search-results', style={
                'minHeight': '200px',
                'padding': '2rem',
                'background': 'rgba(26, 26, 26, 0.5)',
                'borderRadius': '12px',
                'border': '1px solid rgba(222, 181, 34, 0.2)'
            })
        ], style={'maxWidth': '1200px', 'margin': '0 auto'}),

        # Debug 資訊
        html.Div([
            html.H3('Debug Info', style={
                'color': '#ffffff',
                'marginTop': '3rem',
                'marginBottom': '1rem'
            }),
            html.Div(id='debug-info', style={
                'padding': '1rem',
                'background': 'rgba(0, 0, 0, 0.5)',
                'borderRadius': '8px',
                'fontFamily': 'monospace',
                'fontSize': '0.85rem',
                'color': '#deb522'
            })
        ], style={'maxWidth': '1200px', 'margin': '2rem auto'})
    ], style={
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '3rem 2rem',
        'backgroundColor': '#0a0a0a',
        'minHeight': '100vh'
    })
])


# ====== Test Callbacks ======

# 1. 測試搜尋建議
@app.callback(
    [Output('search-suggestions', 'children'),
     Output('search-suggestions', 'style'),
     Output('clear-search-btn', 'style')],
    [Input('search-destination', 'value')],
    prevent_initial_call=False
)
def test_search_suggestions(keyword):
    """測試即時搜尋建議功能"""
    if not keyword or len(keyword) < 2:
        return [], {'display': 'none'}, {'display': 'none'}

    suggestions = generate_search_suggestions(keyword, restaurants_df, max_results=8)

    if not suggestions:
        return (
            [html.Div('No suggestions found', style={'padding': '1rem', 'textAlign': 'center', 'color': '#888'})],
            {'display': 'block'},
            {'display': 'block'}
        )

    suggestion_items = []
    for sugg in suggestions:
        suggestion_items.append(
            create_suggestion_item(
                text=sugg['text'],
                category=sugg['category'],
                icon=sugg['icon']
            )
        )

    return suggestion_items, {'display': 'block'}, {'display': 'block'}


# 2. 測試進階篩選器切換
@app.callback(
    [Output('advanced-filters-collapse', 'is_open'),
     Output('toggle-advanced-filters', 'className'),
     Output('filters-open-state', 'data')],
    [Input('toggle-advanced-filters', 'n_clicks')],
    [State('filters-open-state', 'data')],
    prevent_initial_call=True
)
def test_toggle_filters(n_clicks, is_open):
    """測試進階篩選器切換"""
    if not n_clicks:
        return no_update, no_update, no_update

    new_state = not is_open
    button_class = 'filter-toggle-btn active' if new_state else 'filter-toggle-btn'
    return new_state, button_class, new_state


# 3. 測試清除搜尋框
@app.callback(
    Output('search-destination', 'value'),
    [Input('clear-search-btn', 'n_clicks')],
    prevent_initial_call=True
)
def test_clear_search(n_clicks):
    """測試清除搜尋框"""
    if n_clicks:
        return ''
    return no_update


# 4. 測試篩選標籤
@app.callback(
    Output('active-filters-chips', 'children'),
    [Input('search-cuisine', 'value'),
     Input('search-rating', 'value'),
     Input('price-filter', 'value'),
     Input('station-filter', 'value'),
     Input('review-count-filter', 'value')],
    prevent_initial_call=False
)
def test_filter_chips(cuisine, rating, price_filters, stations, min_reviews):
    """測試篩選標籤生成"""
    chips = []

    if cuisine:
        chips.append(create_filter_chip(f'Cuisine: {cuisine}', cuisine, 'cuisine'))

    if rating:
        stars = '⭐' * int(rating)
        chips.append(create_filter_chip(f'Rating: {stars}+', rating, 'rating'))

    if price_filters:
        price_labels = {
            'budget': 'Budget (¥1000-¥1999)',
            'mid': 'Mid-range (¥2000-¥3999)',
            'high': 'Fine Dining (¥4000+)'
        }
        for price in price_filters:
            chips.append(create_filter_chip(price_labels.get(price, price), price, 'price'))

    if stations:
        for station in stations:
            chips.append(create_filter_chip(f'Location: {station}', station, 'station'))

    if min_reviews > 0:
        chips.append(create_filter_chip(f'Min Reviews: {min_reviews}+', min_reviews, 'reviews'))

    return chips if chips else []


# 5. 測試搜尋功能
@app.callback(
    [Output('test-search-results', 'children'),
     Output('debug-info', 'children')],
    [Input('search-btn', 'n_clicks')],
    [State('search-destination', 'value'),
     State('search-cuisine', 'value'),
     State('search-rating', 'value'),
     State('price-filter', 'value'),
     State('station-filter', 'value'),
     State('review-count-filter', 'value'),
     State('sort-by', 'value')],
    prevent_initial_call=True
)
def test_search(n_clicks, keyword, cuisine, rating, price_filters, stations, min_reviews, sort_by):
    """測試完整搜尋功能"""
    if not n_clicks:
        return no_update, no_update

    # 執行搜尋
    filtered_df = restaurants_df.copy()

    # Keyword search
    if keyword:
        keyword_lower = keyword.lower()
        mask = (
            filtered_df['Name'].str.lower().str.contains(keyword_lower, na=False) |
            filtered_df['JapaneseName'].str.contains(keyword, na=False) |
            filtered_df['FirstCategory'].str.lower().str.contains(keyword_lower, na=False) |
            filtered_df['SecondCategory'].str.lower().str.contains(keyword_lower, na=False) |
            filtered_df['Station'].str.lower().str.contains(keyword_lower, na=False)
        )
        filtered_df = filtered_df[mask]

    # Cuisine filter
    if cuisine:
        filtered_df = filtered_df[filtered_df['FirstCategory'] == cuisine]

    # Rating filter
    if rating:
        filtered_df = filtered_df[filtered_df['TotalRating'] >= rating]

    # Station filter
    if stations:
        filtered_df = filtered_df[filtered_df['Station'].isin(stations)]

    # Review count filter
    if min_reviews > 0:
        filtered_df = filtered_df[filtered_df['ReviewNum'] >= min_reviews]

    # Sort
    if sort_by == 'rating_desc':
        filtered_df = filtered_df.sort_values(by=['TotalRating', 'ReviewNum'], ascending=[False, False])
    elif sort_by == 'rating_asc':
        filtered_df = filtered_df.sort_values(by=['TotalRating', 'ReviewNum'], ascending=[True, False])
    elif sort_by == 'reviews':
        filtered_df = filtered_df.sort_values(by=['ReviewNum', 'TotalRating'], ascending=[False, False])
    elif sort_by == 'name':
        filtered_df = filtered_df.sort_values(by='Name', ascending=True)

    # 顯示結果
    if len(filtered_df) == 0:
        results = html.Div([
            html.I(className='fas fa-search', style={'fontSize': '3rem', 'color': '#666', 'marginBottom': '1rem'}),
            html.H4('No restaurants found', style={'color': '#aaa'}),
            html.P('Try adjusting your search criteria', style={'color': '#666'})
        ], style={'textAlign': 'center', 'padding': '3rem'})
    else:
        # 顯示前 10 個結果
        result_cards = []
        for _, row in filtered_df.head(10).iterrows():
            card = html.Div([
                html.Div([
                    html.Span(row['Name'], style={'fontWeight': 'bold', 'fontSize': '1.1rem'}),
                    html.Span(f" {row['TotalRating']:.1f}⭐", style={'color': '#deb522', 'marginLeft': '0.5rem'})
                ]),
                html.Div(f"{row['FirstCategory']} · {row['Station']}", style={
                    'color': '#888',
                    'fontSize': '0.9rem',
                    'marginTop': '0.25rem'
                }),
                html.Div(f"{int(row['ReviewNum'])} reviews", style={
                    'color': '#666',
                    'fontSize': '0.85rem',
                    'marginTop': '0.25rem'
                })
            ], style={
                'padding': '1rem',
                'marginBottom': '0.75rem',
                'background': 'rgba(0, 0, 0, 0.3)',
                'borderRadius': '8px',
                'border': '1px solid rgba(222, 181, 34, 0.2)'
            })
            result_cards.append(card)

        results = html.Div([
            html.Div(f'Found {len(filtered_df)} restaurants (showing top 10)', style={
                'color': '#deb522',
                'marginBottom': '1rem',
                'fontWeight': 'bold'
            }),
            html.Div(result_cards)
        ])

    # Debug 資訊
    debug_text = f"""
Search Parameters:
  Keyword: {keyword or 'None'}
  Cuisine: {cuisine or 'None'}
  Rating: {rating or 'None'}
  Price Filters: {price_filters or 'None'}
  Stations: {stations or 'None'}
  Min Reviews: {min_reviews}
  Sort By: {sort_by}

Results:
  Total Found: {len(filtered_df)}
  First Restaurant: {filtered_df.iloc[0]['Name'] if len(filtered_df) > 0 else 'N/A'}
    """

    return results, html.Pre(debug_text)


# 6. 測試搜尋歷史
@app.callback(
    Output('search-history-list', 'children'),
    [Input('search-btn', 'n_clicks')],
    [State('search-destination', 'value')],
    prevent_initial_call=False
)
def test_search_history(n_clicks, keyword):
    """測試搜尋歷史顯示"""
    # 模擬歷史記錄
    mock_history = [
        ('sushi', '5m ago'),
        ('ramen kyoto station', '15m ago'),
        ('kaiseki', '1h ago'),
        ('tempura', '3h ago'),
        ('izakaya', '1d ago')
    ]

    return [create_history_item(query, time) for query, time in mock_history]


# 7. 測試熱門搜尋
@app.callback(
    Output('popular-searches-list', 'children'),
    [Input('search-btn', 'n_clicks')],
    prevent_initial_call=False
)
def test_popular_searches(n_clicks):
    """測試熱門搜尋顯示"""
    # 模擬熱門搜尋
    mock_popular = [
        ('Sushi', 42),
        ('Ramen', 38),
        ('Kyoto Station', 35),
        ('Kaiseki', 28),
        ('Tempura', 24)
    ]

    return [create_popular_item(term, count) for term, count in mock_popular]


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Enhanced Search System - Test Application")
    print("="*60)
    print("\n測試功能：")
    print("  1. 即時搜尋建議 (輸入 2+ 字元)")
    print("  2. 進階篩選器 (點擊 Filters 按鈕)")
    print("  3. 篩選標籤顯示")
    print("  4. 完整搜尋功能 (點擊 Search)")
    print("  5. 搜尋歷史記錄")
    print("  6. 熱門搜尋列表")
    print("\n訪問: http://127.0.0.1:8050")
    print("="*60 + "\n")

    app.run(debug=True, port=8050)
