"""
Search Callbacks for Enhanced Restaurant Search System
增強搜尋系統的 Callback 函數

功能包括:
1. 即時搜尋建議 (Real-time Search Suggestions)
2. 進階篩選器切換 (Advanced Filters Toggle)
3. 篩選標籤管理 (Filter Chips Management)
4. 搜尋歷史記錄 (Search History)
5. 熱門搜尋統計 (Popular Searches)
6. 即時搜尋 (Live Search with Debounce)
"""

from dash import Input, Output, State, callback_context, no_update, ALL
from dash.exceptions import PreventUpdate
import pandas as pd
from datetime import datetime, timedelta

from components.enhanced_search import (
    create_suggestion_item,
    create_filter_chip,
    create_history_item,
    create_popular_item,
    generate_search_suggestions,
    apply_advanced_filters,
    add_to_search_history,
    update_popular_searches,
    get_top_popular_searches
)


def register_search_callbacks(app, restaurants_df):
    """
    註冊所有搜尋相關的 callbacks

    Args:
        app: Dash app instance
        restaurants_df: 餐廳資料 DataFrame
    """

    # ====== 1. 即時搜尋建議 ======
    @app.callback(
        [Output('search-suggestions', 'children'),
         Output('search-suggestions', 'style'),
         Output('clear-search-btn', 'style')],
        [Input('search-destination', 'value')],
        prevent_initial_call=False
    )
    def update_search_suggestions(keyword):
        """
        根據使用者輸入即時生成搜尋建議

        Inputs:
            - search-destination.value: 使用者輸入的關鍵字

        Outputs:
            - search-suggestions.children: 建議列表組件
            - search-suggestions.style: 顯示/隱藏建議框
            - clear-search-btn.style: 顯示/隱藏清除按鈕
        """
        if not keyword or len(keyword) < 2:
            return [], {'display': 'none'}, {'display': 'none'}

        # 生成建議
        suggestions = generate_search_suggestions(keyword, restaurants_df, max_results=8)

        if not suggestions:
            return (
                [html.Div([
                    html.I(className='fas fa-search', style={'color': '#666', 'marginRight': '8px'}),
                    html.Span('No suggestions found', style={'color': '#888'})
                ], style={'padding': '1rem', 'textAlign': 'center'})],
                {'display': 'block'},
                {'display': 'block'}
            )

        # 創建建議項目
        suggestion_items = []
        for sugg in suggestions:
            suggestion_items.append(
                create_suggestion_item(
                    text=sugg['text'],
                    category=sugg['category'],
                    icon=sugg['icon']
                )
            )

        return (
            suggestion_items,
            {'display': 'block'},
            {'display': 'block'}
        )


    # ====== 2. 進階篩選器切換 ======
    @app.callback(
        [Output('advanced-filters-collapse', 'is_open'),
         Output('toggle-advanced-filters', 'className'),
         Output('filters-open-state', 'data')],
        [Input('toggle-advanced-filters', 'n_clicks')],
        [State('filters-open-state', 'data')],
        prevent_initial_call=True
    )
    def toggle_advanced_filters(n_clicks, is_open):
        """
        切換進階篩選器的顯示/隱藏

        Inputs:
            - toggle-advanced-filters.n_clicks: 按鈕點擊

        States:
            - filters-open-state.data: 當前開關狀態

        Outputs:
            - advanced-filters-collapse.is_open: 摺疊組件狀態
            - toggle-advanced-filters.className: 按鈕樣式
            - filters-open-state.data: 更新狀態
        """
        if not n_clicks:
            raise PreventUpdate

        new_state = not is_open
        button_class = 'filter-toggle-btn active' if new_state else 'filter-toggle-btn'

        return new_state, button_class, new_state


    # ====== 3. 清除搜尋框 ======
    @app.callback(
        Output('search-destination', 'value'),
        [Input('clear-search-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def clear_search_input(n_clicks):
        """清除搜尋輸入框"""
        if n_clicks:
            return ''
        raise PreventUpdate


    # ====== 4. 清除所有篩選器 ======
    @app.callback(
        [Output('search-cuisine', 'value'),
         Output('search-rating', 'value'),
         Output('price-filter', 'value'),
         Output('station-filter', 'value'),
         Output('review-count-filter', 'value'),
         Output('sort-by', 'value')],
        [Input('clear-filters-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def clear_all_filters(n_clicks):
        """
        清除所有篩選器設定

        Inputs:
            - clear-filters-btn.n_clicks: 清除按鈕點擊

        Outputs:
            - 所有篩選器組件的 value: 重設為預設值
        """
        if n_clicks:
            return None, None, [], [], 0, 'rating_desc'
        raise PreventUpdate


    # ====== 5. 生成活躍篩選標籤 ======
    @app.callback(
        Output('active-filters-chips', 'children'),
        [Input('search-cuisine', 'value'),
         Input('search-rating', 'value'),
         Input('price-filter', 'value'),
         Input('station-filter', 'value'),
         Input('review-count-filter', 'value')],
        prevent_initial_call=False
    )
    def update_filter_chips(cuisine, rating, price_filters, stations, min_reviews):
        """
        根據當前篩選器狀態生成篩選標籤

        Inputs:
            - 所有篩選器的當前值

        Outputs:
            - active-filters-chips.children: 篩選標籤列表
        """
        chips = []

        # Cuisine chip
        if cuisine:
            chips.append(create_filter_chip(
                label=f'Cuisine: {cuisine}',
                value=cuisine,
                filter_type='cuisine'
            ))

        # Rating chip
        if rating:
            stars = '⭐' * int(rating)
            chips.append(create_filter_chip(
                label=f'Rating: {stars}+',
                value=rating,
                filter_type='rating'
            ))

        # Price chips
        if price_filters:
            price_labels = {
                'budget': 'Budget (¥1000-¥1999)',
                'mid': 'Mid-range (¥2000-¥3999)',
                'high': 'Fine Dining (¥4000+)'
            }
            for price in price_filters:
                chips.append(create_filter_chip(
                    label=price_labels.get(price, price),
                    value=price,
                    filter_type='price'
                ))

        # Station chips
        if stations:
            for station in stations:
                chips.append(create_filter_chip(
                    label=f'Location: {station}',
                    value=station,
                    filter_type='station'
                ))

        # Review count chip
        if min_reviews > 0:
            chips.append(create_filter_chip(
                label=f'Min Reviews: {min_reviews}+',
                value=min_reviews,
                filter_type='reviews'
            ))

        return chips if chips else []


    # ====== 6. 移除單個篩選標籤 ======
    @app.callback(
        [Output('search-cuisine', 'value', allow_duplicate=True),
         Output('search-rating', 'value', allow_duplicate=True),
         Output('price-filter', 'value', allow_duplicate=True),
         Output('station-filter', 'value', allow_duplicate=True),
         Output('review-count-filter', 'value', allow_duplicate=True)],
        [Input({'type': 'remove-filter', 'filter': ALL, 'value': ALL}, 'n_clicks')],
        [State('search-cuisine', 'value'),
         State('search-rating', 'value'),
         State('price-filter', 'value'),
         State('station-filter', 'value'),
         State('review-count-filter', 'value')],
        prevent_initial_call=True
    )
    def remove_filter_chip(n_clicks_list, current_cuisine, current_rating,
                          current_price, current_stations, current_reviews):
        """
        移除單個篩選標籤

        使用 Pattern Matching Callbacks (ALL) 來處理動態生成的標籤

        Inputs:
            - remove-filter button clicks (pattern matching)

        States:
            - 所有篩選器的當前值

        Outputs:
            - 更新對應的篩選器值
        """
        ctx = callback_context

        if not ctx.triggered or not any(n_clicks_list):
            raise PreventUpdate

        # 解析被點擊的按鈕
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        import json
        button_data = json.loads(button_id)
        filter_type = button_data['filter']
        filter_value = button_data['value']

        # 根據 filter_type 移除對應的值
        if filter_type == 'cuisine':
            return None, current_rating, current_price, current_stations, current_reviews

        elif filter_type == 'rating':
            return current_cuisine, None, current_price, current_stations, current_reviews

        elif filter_type == 'price':
            new_price = [p for p in current_price if p != filter_value]
            return current_cuisine, current_rating, new_price, current_stations, current_reviews

        elif filter_type == 'station':
            new_stations = [s for s in current_stations if s != filter_value]
            return current_cuisine, current_rating, current_price, new_stations, current_reviews

        elif filter_type == 'reviews':
            return current_cuisine, current_rating, current_price, current_stations, 0

        raise PreventUpdate


    # ====== 7. 主搜尋功能 (with History & Popular) ======
    @app.callback(
        [Output('search-results-store', 'data'),
         Output('current-page-store', 'data'),
         Output('search-params-store', 'data'),
         Output('search-history-store', 'data'),
         Output('popular-searches-store', 'data')],
        [Input('search-btn', 'n_clicks'),
         Input('search-trigger', 'data')],  # 即時搜尋觸發器
        [State('search-destination', 'value'),
         State('search-cuisine', 'value'),
         State('search-rating', 'value'),
         State('price-filter', 'value'),
         State('station-filter', 'value'),
         State('review-count-filter', 'value'),
         State('sort-by', 'value'),
         State('search-history-store', 'data'),
         State('popular-searches-store', 'data'),
         State('view-mode', 'data')],
        prevent_initial_call=True
    )
    def handle_comprehensive_search(search_click, search_trigger,
                                   keyword, cuisine, rating,
                                   price_filters, stations, min_reviews, sort_by,
                                   history, popular_dict, view_mode):
        """
        處理完整的搜尋功能（包含歷史記錄和熱門統計）

        Inputs:
            - search-btn.n_clicks: 搜尋按鈕點擊
            - search-trigger.data: 即時搜尋觸發（用於自動搜尋）
            - 所有篩選器的當前值

        States:
            - search-history-store.data: 搜尋歷史
            - popular-searches-store.data: 熱門搜尋
            - view-mode.data: 當前頁面模式

        Outputs:
            - search-results-store.data: 搜尋結果
            - current-page-store.data: 重設為第 1 頁
            - search-params-store.data: 搜尋參數
            - search-history-store.data: 更新搜尋歷史
            - popular-searches-store.data: 更新熱門搜尋
        """
        ctx = callback_context

        # 只在餐廳列表頁執行
        if view_mode != 'restaurant-list' and not search_click:
            raise PreventUpdate

        # Step 1: 基礎搜尋 (關鍵字 + 料理 + 評分)
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

        # Step 2: 應用進階篩選器
        filtered_df = apply_advanced_filters(
            filtered_df,
            price_filters=price_filters or [],
            stations=stations or [],
            min_reviews=min_reviews or 0,
            sort_by=sort_by or 'rating_desc'
        )

        # Step 3: 更新搜尋歷史
        search_filters = {
            'cuisine': cuisine,
            'rating': rating,
            'price': price_filters,
            'stations': stations,
            'min_reviews': min_reviews
        }
        updated_history = add_to_search_history(history, keyword, search_filters)

        # Step 4: 更新熱門搜尋
        updated_popular = popular_dict or {}
        if keyword:
            updated_popular = update_popular_searches(updated_popular, keyword, 'query')
        if cuisine:
            updated_popular = update_popular_searches(updated_popular, cuisine, 'cuisine')
        if stations:
            for station in stations:
                updated_popular = update_popular_searches(updated_popular, station, 'station')

        # Step 5: 準備返回結果
        search_results = filtered_df.to_dict('records') if len(filtered_df) > 0 else []
        search_params = {
            'keyword': keyword,
            'cuisine': cuisine,
            'rating': rating,
            'price_filters': price_filters,
            'stations': stations,
            'min_reviews': min_reviews,
            'sort_by': sort_by
        }

        return search_results, 1, search_params, updated_history, updated_popular


    # ====== 8. 顯示搜尋歷史 ======
    @app.callback(
        Output('search-history-list', 'children'),
        [Input('search-history-store', 'data')],
        prevent_initial_call=False
    )
    def display_search_history(history):
        """
        顯示搜尋歷史列表

        Inputs:
            - search-history-store.data: 搜尋歷史

        Outputs:
            - search-history-list.children: 歷史列表組件
        """
        if not history or len(history) == 0:
            return html.Div([
                html.Span('No recent searches', style={
                    'color': '#666',
                    'fontSize': '0.9rem',
                    'fontStyle': 'italic'
                })
            ])

        history_items = []
        for record in history[:5]:  # 只顯示最近 5 筆
            query = record.get('query', 'Unknown')
            timestamp = record.get('timestamp', '')

            # 簡化時間顯示
            try:
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                diff = now - dt

                if diff.total_seconds() < 3600:
                    time_str = f"{int(diff.total_seconds() / 60)}m ago"
                elif diff.total_seconds() < 86400:
                    time_str = f"{int(diff.total_seconds() / 3600)}h ago"
                else:
                    time_str = f"{diff.days}d ago"
            except:
                time_str = 'Recently'

            history_items.append(create_history_item(query or 'Browse all', time_str))

        return history_items


    # ====== 9. 顯示熱門搜尋 ======
    @app.callback(
        Output('popular-searches-list', 'children'),
        [Input('popular-searches-store', 'data')],
        prevent_initial_call=False
    )
    def display_popular_searches(popular_dict):
        """
        顯示熱門搜尋列表

        Inputs:
            - popular-searches-store.data: 熱門搜尋字典

        Outputs:
            - popular-searches-list.children: 熱門列表組件
        """
        if not popular_dict or len(popular_dict) == 0:
            # 顯示預設熱門項目
            default_popular = [
                ('Sushi', 42),
                ('Ramen', 38),
                ('Kyoto Station', 35),
                ('Kaiseki', 28),
                ('Tempura', 24)
            ]
            return [create_popular_item(term, count) for term, count in default_popular]

        top_searches = get_top_popular_searches(popular_dict, top_n=5)

        if not top_searches:
            return html.Div([
                html.Span('No popular searches yet', style={
                    'color': '#666',
                    'fontSize': '0.9rem',
                    'fontStyle': 'italic'
                })
            ])

        return [create_popular_item(term, count) for term, count in top_searches]


    # ====== 10. 點擊歷史項目重新搜尋 ======
    @app.callback(
        [Output('search-destination', 'value', allow_duplicate=True),
         Output('search-trigger', 'data')],
        [Input({'type': 'history-item', 'query': ALL}, 'n_clicks')],
        prevent_initial_call=True
    )
    def replay_history_search(n_clicks_list):
        """
        點擊歷史項目時，重新執行該搜尋

        Inputs:
            - history-item clicks (pattern matching)

        Outputs:
            - search-destination.value: 填入關鍵字
            - search-trigger.data: 觸發搜尋
        """
        ctx = callback_context

        if not ctx.triggered or not any(n_clicks_list):
            raise PreventUpdate

        # 解析被點擊的歷史項目
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        import json
        button_data = json.loads(button_id)
        query = button_data['query']

        return query, datetime.now().timestamp()


    # ====== 11. 點擊熱門項目搜尋 ======
    @app.callback(
        [Output('search-destination', 'value', allow_duplicate=True),
         Output('search-trigger', 'data', allow_duplicate=True)],
        [Input({'type': 'popular-item', 'query': ALL}, 'n_clicks')],
        prevent_initial_call=True
    )
    def search_popular_term(n_clicks_list):
        """
        點擊熱門搜尋項目時，執行搜尋

        Inputs:
            - popular-item clicks (pattern matching)

        Outputs:
            - search-destination.value: 填入關鍵字
            - search-trigger.data: 觸發搜尋
        """
        ctx = callback_context

        if not ctx.triggered or not any(n_clicks_list):
            raise PreventUpdate

        # 解析被點擊的熱門項目
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        import json
        button_data = json.loads(button_id)
        query = button_data['query']

        return query, datetime.now().timestamp()


    # ====== 12. 即時搜尋 (Optional - 可選功能) ======
    @app.callback(
        Output('search-trigger', 'data', allow_duplicate=True),
        [Input('search-destination', 'value'),
         Input('search-cuisine', 'value'),
         Input('search-rating', 'value')],
        prevent_initial_call=True
    )
    def trigger_live_search(keyword, cuisine, rating):
        """
        當輸入改變時自動觸發搜尋（防抖動已在組件設定）

        注意: 這是可選功能，如果不需要即時搜尋可以移除此 callback

        Inputs:
            - search-destination.value: 關鍵字輸入
            - search-cuisine.value: 料理類型
            - search-rating.value: 評分

        Outputs:
            - search-trigger.data: 觸發搜尋 callback
        """
        # 只有在餐廳列表頁且有輸入時才觸發
        if keyword or cuisine or rating:
            return datetime.now().timestamp()
        raise PreventUpdate


    # ====== 13. 顯示搜尋側邊欄 (當有輸入時) ======
    @app.callback(
        Output('search-sidebar', 'style'),
        [Input('search-destination', 'value'),
         Input('view-mode', 'data')],
        prevent_initial_call=False
    )
    def toggle_search_sidebar(keyword, view_mode):
        """
        在首頁顯示搜尋側邊欄（歷史和熱門）

        Inputs:
            - search-destination.value: 關鍵字輸入
            - view-mode.data: 當前頁面

        Outputs:
            - search-sidebar.style: 顯示/隱藏側邊欄
        """
        # 只在首頁且有輸入時顯示
        if view_mode == 'home' and keyword and len(keyword) >= 2:
            return {'display': 'grid'}
        return {'display': 'none'}


# 導入必要的 html 模組
from dash import html
