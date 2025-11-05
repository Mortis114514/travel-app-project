"""
Enhanced Search Components for Voyage Restaurant Search
優化的餐廳搜尋組件 - 包含即時建議、進階篩選、搜尋歷史
"""

from dash import html, dcc
import pandas as pd


def create_enhanced_search_bar(restaurants_df):
    """
    創建增強版複合式搜尋欄

    功能：
    - 即時搜尋建議 (Search Suggestions)
    - 進階篩選器 (Advanced Filters)
    - 搜尋歷史 (Search History)
    - 熱門搜尋 (Popular Searches)
    """

    # 準備料理類型選項
    cuisine_options = [{'label': cat, 'value': cat}
                      for cat in restaurants_df['FirstCategory'].dropna().unique()]

    # 準備車站/地點選項
    station_options = [{'label': station, 'value': station}
                      for station in restaurants_df['Station'].dropna().unique()]

    return html.Div([
        # ===== 主搜尋欄 =====
        html.Div([
            # 關鍵字輸入 with Suggestions
            html.Div([
                html.Div([
                    html.I(className='fas fa-search'),
                    dcc.Input(
                        id='search-destination',
                        type='text',
                        placeholder='Search restaurants, cuisine, or location...',
                        className='search-input',
                        debounce=300,  # 300ms 防抖動
                        autoComplete='off'
                    ),
                    # Clear button
                    html.Button([
                        html.I(className='fas fa-times')
                    ], id='clear-search-btn', className='clear-btn',
                       style={'display': 'none'})
                ], className='search-input-group', style={'position': 'relative'}),

                # Suggestions Dropdown (動態顯示)
                html.Div(id='search-suggestions', className='suggestions-dropdown')
            ], style={'position': 'relative', 'flex': '2'}),

            # Cuisine Dropdown
            html.Div([
                html.I(className='fas fa-utensils'),
                dcc.Dropdown(
                    id='search-cuisine',
                    options=cuisine_options,
                    placeholder='Cuisine Type',
                    className='search-input',
                    style={'border': 'none', 'background': 'transparent'},
                    clearable=True
                )
            ], className='search-input-group', style={'flex': '1'}),

            # Rating Dropdown
            html.Div([
                html.I(className='fas fa-star'),
                dcc.Dropdown(
                    id='search-rating',
                    options=[
                        {'label': '⭐⭐⭐⭐⭐ 5 Stars', 'value': 5},
                        {'label': '⭐⭐⭐⭐ 4+ Stars', 'value': 4},
                        {'label': '⭐⭐⭐ 3+ Stars', 'value': 3}
                    ],
                    placeholder='Rating',
                    className='search-input',
                    style={'border': 'none', 'background': 'transparent'},
                    clearable=True
                )
            ], className='search-input-group', style={'flex': '1'}),

            # Advanced Filter Toggle Button
            html.Button([
                html.I(className='fas fa-sliders-h', style={'marginRight': '8px'}),
                'Filters'
            ], id='toggle-advanced-filters', className='filter-toggle-btn', n_clicks=0),

            # Search Button
            html.Button([
                html.I(className='fas fa-search', style={'marginRight': '8px'}),
                'Search'
            ], id='search-btn', className='search-btn', n_clicks=0)
        ], className='search-container'),

        # ===== 進階篩選器區塊 (可摺疊) =====
        html.Div([
            dcc.Collapse(
                html.Div([
                    html.Div([
                        # 價格範圍篩選
                        html.Div([
                            html.Label([
                                html.I(className='fas fa-yen-sign',
                                      style={'marginRight': '8px', 'color': '#deb522'}),
                                'Price Range'
                            ], className='filter-label'),
                            dcc.Checklist(
                                id='price-filter',
                                options=[
                                    {'label': ' Budget (¥1000-¥1999)', 'value': 'budget'},
                                    {'label': ' Mid-range (¥2000-¥3999)', 'value': 'mid'},
                                    {'label': ' Fine Dining (¥4000+)', 'value': 'high'}
                                ],
                                value=[],
                                className='filter-checklist',
                                labelStyle={'display': 'block', 'marginBottom': '0.5rem'}
                            )
                        ], className='filter-group'),

                        # 地點篩選
                        html.Div([
                            html.Label([
                                html.I(className='fas fa-map-marker-alt',
                                      style={'marginRight': '8px', 'color': '#deb522'}),
                                'Location / Station'
                            ], className='filter-label'),
                            dcc.Dropdown(
                                id='station-filter',
                                options=station_options,
                                placeholder='Select station...',
                                className='filter-dropdown',
                                multi=True,
                                clearable=True
                            )
                        ], className='filter-group'),

                        # 評論數量篩選
                        html.Div([
                            html.Label([
                                html.I(className='fas fa-comment',
                                      style={'marginRight': '8px', 'color': '#deb522'}),
                                'Minimum Reviews'
                            ], className='filter-label'),
                            dcc.Slider(
                                id='review-count-filter',
                                min=0,
                                max=200,
                                step=10,
                                value=0,
                                marks={
                                    0: '0',
                                    50: '50',
                                    100: '100',
                                    150: '150',
                                    200: '200+'
                                },
                                tooltip={"placement": "bottom", "always_visible": False},
                                className='filter-slider'
                            )
                        ], className='filter-group'),

                        # 排序選項
                        html.Div([
                            html.Label([
                                html.I(className='fas fa-sort',
                                      style={'marginRight': '8px', 'color': '#deb522'}),
                                'Sort By'
                            ], className='filter-label'),
                            dcc.RadioItems(
                                id='sort-by',
                                options=[
                                    {'label': ' Rating (High to Low)', 'value': 'rating_desc'},
                                    {'label': ' Rating (Low to High)', 'value': 'rating_asc'},
                                    {'label': ' Review Count', 'value': 'reviews'},
                                    {'label': ' Name (A-Z)', 'value': 'name'}
                                ],
                                value='rating_desc',
                                className='filter-radioitems',
                                labelStyle={'display': 'block', 'marginBottom': '0.5rem'}
                            )
                        ], className='filter-group'),

                    ], className='advanced-filters-grid'),

                    # Clear all filters button
                    html.Div([
                        html.Button([
                            html.I(className='fas fa-undo', style={'marginRight': '8px'}),
                            'Clear All Filters'
                        ], id='clear-filters-btn', className='btn-secondary', n_clicks=0)
                    ], style={'textAlign': 'right', 'marginTop': '1rem'})
                ], className='advanced-filters-container'),
                id='advanced-filters-collapse',
                is_open=False
            )
        ], id='advanced-filters-wrapper'),

        # ===== 活躍篩選標籤 (Filter Chips) =====
        html.Div(id='active-filters-chips', className='filter-chips-container'),

        # ===== 搜尋歷史與熱門搜尋 =====
        html.Div([
            # 搜尋歷史
            html.Div([
                html.Div([
                    html.I(className='fas fa-history', style={'marginRight': '8px'}),
                    html.Span('Recent Searches')
                ], className='sidebar-title'),
                html.Div(id='search-history-list', className='history-list')
            ], className='search-sidebar-section'),

            # 熱門搜尋
            html.Div([
                html.Div([
                    html.I(className='fas fa-fire', style={'marginRight': '8px', 'color': '#deb522'}),
                    html.Span('Popular Searches')
                ], className='sidebar-title'),
                html.Div(id='popular-searches-list', className='popular-list')
            ], className='search-sidebar-section')
        ], id='search-sidebar', className='search-sidebar', style={'display': 'none'})
    ])


def create_suggestion_item(text, category, icon='fa-utensils'):
    """創建搜尋建議項目"""
    return html.Div([
        html.Div([
            html.I(className=f'fas {icon}', style={'color': '#deb522', 'width': '20px'}),
            html.Span(text, className='suggestion-text')
        ], className='suggestion-main'),
        html.Span(category, className='suggestion-category')
    ], className='suggestion-item')


def create_filter_chip(label, value, filter_type):
    """創建篩選標籤 (可移除)"""
    return html.Div([
        html.Span(label, style={'marginRight': '8px'}),
        html.Button([
            html.I(className='fas fa-times')
        ], id={'type': 'remove-filter', 'filter': filter_type, 'value': value},
           className='chip-remove-btn', n_clicks=0)
    ], className='filter-chip')


def create_history_item(query, timestamp):
    """創建搜尋歷史項目"""
    return html.Div([
        html.Div([
            html.I(className='fas fa-search', style={'color': '#888', 'marginRight': '8px'}),
            html.Span(query, className='history-text')
        ], style={'flex': '1'}),
        html.Span(timestamp, className='history-time')
    ], className='history-item', id={'type': 'history-item', 'query': query}, n_clicks=0)


def create_popular_item(label, count):
    """創建熱門搜尋項目"""
    return html.Div([
        html.Div([
            html.Span(label, className='popular-text'),
            html.Span(f'{count} searches', className='popular-count')
        ], style={'flex': '1'}),
        html.I(className='fas fa-arrow-right', style={'color': '#deb522'})
    ], className='popular-item', id={'type': 'popular-item', 'query': label}, n_clicks=0)


# ===== Data Store Components =====
def create_search_stores():
    """
    創建搜尋相關的 dcc.Store 組件

    Stores:
    - search-history-store: 搜尋歷史 (list of dict)
    - search-suggestions-store: 即時搜尋建議 (list of dict)
    - active-filters-store: 當前活躍的篩選器 (dict)
    - popular-searches-store: 熱門搜尋統計 (dict)
    """
    return html.Div([
        # 搜尋歷史 (session storage - 保留到瀏覽器關閉)
        dcc.Store(id='search-history-store', storage_type='session', data=[]),

        # 搜尋建議 (memory - 即時計算)
        dcc.Store(id='search-suggestions-store', storage_type='memory', data=[]),

        # 活躍篩選器 (memory - 當前搜尋狀態)
        dcc.Store(id='active-filters-store', storage_type='memory', data={}),

        # 熱門搜尋 (local storage - 長期保存)
        dcc.Store(id='popular-searches-store', storage_type='local', data={}),

        # 即時搜尋觸發器 (memory - 用於防抖動)
        dcc.Store(id='search-trigger', storage_type='memory'),

        # 篩選器展開狀態
        dcc.Store(id='filters-open-state', storage_type='memory', data=False)
    ])


# ===== Helper Function for Search Logic =====
def get_price_category(price_str):
    """
    從價格字串判斷價格類別

    Args:
        price_str: 例如 "¥2000~¥2999"

    Returns:
        'budget', 'mid', 'high', or None
    """
    if pd.isna(price_str) or price_str == 'NaN':
        return None

    price_str = str(price_str)

    if '¥1000' in price_str or '¥1999' in price_str:
        return 'budget'
    elif '¥2000' in price_str or '¥3000' in price_str or '¥3999' in price_str:
        return 'mid'
    elif '¥4000' in price_str or '¥5000' in price_str:
        return 'high'

    return None


def generate_search_suggestions(keyword, restaurants_df, max_results=8):
    """
    生成搜尋建議

    Args:
        keyword: 使用者輸入的關鍵字
        restaurants_df: 餐廳資料 DataFrame
        max_results: 最多返回多少建議

    Returns:
        List of dicts with format:
        [
            {'text': '建議文字', 'category': '類別', 'icon': 'fa-icon', 'type': 'restaurant/cuisine/station'},
            ...
        ]
    """
    if not keyword or len(keyword) < 2:
        return []

    suggestions = []
    keyword_lower = keyword.lower()

    # 1. 搜尋餐廳名稱
    name_matches = restaurants_df[
        restaurants_df['Name'].str.lower().str.contains(keyword_lower, na=False)
    ].head(3)

    for _, row in name_matches.iterrows():
        suggestions.append({
            'text': row['Name'],
            'category': f"{row['FirstCategory']} · {row['Station']}",
            'icon': 'fa-store',
            'type': 'restaurant',
            'value': row['Name']
        })

    # 2. 搜尋料理類型
    cuisine_matches = restaurants_df[
        restaurants_df['FirstCategory'].str.lower().str.contains(keyword_lower, na=False)
    ]['FirstCategory'].unique()[:3]

    for cuisine in cuisine_matches:
        count = len(restaurants_df[restaurants_df['FirstCategory'] == cuisine])
        suggestions.append({
            'text': cuisine,
            'category': f'{count} restaurants',
            'icon': 'fa-utensils',
            'type': 'cuisine',
            'value': cuisine
        })

    # 3. 搜尋地點/車站
    station_matches = restaurants_df[
        restaurants_df['Station'].str.lower().str.contains(keyword_lower, na=False)
    ]['Station'].unique()[:2]

    for station in station_matches:
        count = len(restaurants_df[restaurants_df['Station'] == station])
        suggestions.append({
            'text': station,
            'category': f'{count} restaurants',
            'icon': 'fa-map-marker-alt',
            'type': 'station',
            'value': station
        })

    return suggestions[:max_results]


def apply_advanced_filters(df, price_filters, stations, min_reviews, sort_by):
    """
    應用進階篩選器

    Args:
        df: 餐廳 DataFrame
        price_filters: list of 'budget', 'mid', 'high'
        stations: list of station names
        min_reviews: int, 最少評論數
        sort_by: 'rating_desc', 'rating_asc', 'reviews', 'name'

    Returns:
        Filtered and sorted DataFrame
    """
    filtered_df = df.copy()

    # 價格篩選
    if price_filters and len(price_filters) > 0:
        # 為每個餐廳計算價格類別
        filtered_df['price_cat'] = filtered_df['DinnerPrice'].apply(get_price_category)
        filtered_df = filtered_df[filtered_df['price_cat'].isin(price_filters)]
        filtered_df = filtered_df.drop('price_cat', axis=1)

    # 地點篩選
    if stations and len(stations) > 0:
        filtered_df = filtered_df[filtered_df['Station'].isin(stations)]

    # 評論數篩選
    if min_reviews > 0:
        filtered_df = filtered_df[filtered_df['ReviewNum'] >= min_reviews]

    # 排序
    if sort_by == 'rating_desc':
        filtered_df = filtered_df.sort_values(
            by=['TotalRating', 'ReviewNum'], ascending=[False, False]
        )
    elif sort_by == 'rating_asc':
        filtered_df = filtered_df.sort_values(
            by=['TotalRating', 'ReviewNum'], ascending=[True, False]
        )
    elif sort_by == 'reviews':
        filtered_df = filtered_df.sort_values(
            by=['ReviewNum', 'TotalRating'], ascending=[False, False]
        )
    elif sort_by == 'name':
        filtered_df = filtered_df.sort_values(by='Name', ascending=True)

    return filtered_df


def add_to_search_history(history, query, filters):
    """
    添加搜尋記錄到歷史

    Args:
        history: 現有歷史 list
        query: 搜尋關鍵字
        filters: 篩選器字典

    Returns:
        Updated history list (最多保留 10 筆)
    """
    from datetime import datetime

    if not history:
        history = []

    # 建立新記錄
    new_record = {
        'query': query or '',
        'filters': filters,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 避免重複（如果完全相同的搜尋）
    for record in history:
        if (record.get('query') == new_record['query'] and
            record.get('filters') == new_record['filters']):
            history.remove(record)
            break

    # 添加到最前面
    history.insert(0, new_record)

    # 只保留最近 10 筆
    return history[:10]


def update_popular_searches(popular_dict, search_term, search_type='query'):
    """
    更新熱門搜尋統計

    Args:
        popular_dict: 現有熱門搜尋字典
        search_term: 搜尋詞
        search_type: 'query', 'cuisine', 'station'

    Returns:
        Updated popular_dict
    """
    if not popular_dict:
        popular_dict = {}

    if not search_term:
        return popular_dict

    key = f"{search_type}:{search_term}"

    if key in popular_dict:
        popular_dict[key]['count'] += 1
    else:
        popular_dict[key] = {
            'term': search_term,
            'type': search_type,
            'count': 1
        }

    return popular_dict


def get_top_popular_searches(popular_dict, top_n=5):
    """
    獲取最熱門的搜尋詞

    Args:
        popular_dict: 熱門搜尋字典
        top_n: 返回前 N 個

    Returns:
        List of tuples (term, count)
    """
    if not popular_dict:
        return []

    # 排序並取前 N 個
    sorted_items = sorted(
        popular_dict.values(),
        key=lambda x: x['count'],
        reverse=True
    )

    return [(item['term'], item['count']) for item in sorted_items[:top_n]]
