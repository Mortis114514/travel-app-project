# Import 所有相關套件
import dash
from dash import Dash, html, dcc, Input, State, Output, dash_table, no_update, callback_context, ALL, MATCH
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import dash_leaflet as dl
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import uuid
import random
import json
from datetime import datetime, timedelta

# 從./utils導入所有自定義函數
from utils.auth import verify_user, create_user, get_session, create_session, delete_session, clean_expired_sessions, get_user_full_details
from pages.login_page import create_login_layout, create_register_layout
from pages.analytics_page import create_analytics_layout, load_and_prepare_data, register_analytics_callbacks
from utils.database import get_revenue_trend, get_occupancy_status

########################
#### 資料載入與前處理 ####
########################
# 導入數據庫工具
from utils.database import (
    get_all_restaurants,
    get_random_top_restaurants as db_get_random_top_restaurants,
    search_restaurants as db_search_restaurants,
    get_unique_stations,
    get_unique_cuisines,
    get_restaurants_by_category,
    get_restaurant_by_id,
    get_nearby_restaurants,
    get_all_hotels,
    get_hotel_by_id,
    get_random_top_hotels,
    search_hotels,
    get_unique_hotel_types,
    get_nearby_hotels,
    get_hotels_by_type
)


restaurants_df = get_all_restaurants()  # 從數據庫加載（用於選項列表）
hotels_df = get_all_hotels()
analytics_df = load_and_prepare_data()


# 隨機選擇4-5星餐廳（使用數據庫查詢）
def get_random_top_restaurants(n=5):
    """從4-5星餐廳中隨機選擇n個餐廳（數據庫版本）"""
    # 使用數據庫查詢獲取隨機高評分餐廳
    return db_get_random_top_restaurants(n=n, min_rating=4.0)

# 移除類別名稱中的括號內容
def remove_parentheses(text):
    """移除字符串中的括號及其內容
    例如: "Izakaya (Tavern)" -> "Izakaya"
    """
    import re
    if pd.isna(text):
        return text
    # 移除括號及其內容，並去除多餘空格
    return re.sub(r'\s*\([^)]*\)', '', str(text)).strip()

def create_cuisine_options():
    """創建料理類型選項列表（包含清除選項）- 使用數據庫數據"""
    options = []
    # 清除選擇選項
    options.append(
        html.Div([
            html.I(className='fas fa-times', style={'marginRight': '8px'}),
            'Clear Selection'
        ],
        className='custom-dropdown-item',
        id={'type': 'cuisine-option', 'index': '__CLEAR__'},
        n_clicks=0,
        style={'borderBottom': '2px solid rgba(222, 181, 34, 0.3)', 'fontWeight': '500'})
    )

    # 從數據庫獲取唯一的料理類型
    seen_labels = {}
    all_categories = get_unique_cuisines()

    # 其他選項
    for cat in all_categories:
        display_label = remove_parentheses(cat)
        # 只添加第一次出現的顯示文本
        if display_label not in seen_labels:
            seen_labels[display_label] = cat
            options.append(
                html.Div(display_label,
                        className='custom-dropdown-item',
                        id={'type': 'cuisine-option', 'index': cat},
                        n_clicks=0)
            )
    return options

def create_rating_options():
    """創建評分選項列表（包含清除選項）"""
    options = []
    # 清除選擇選項
    options.append(
        html.Div([
            html.I(className='fas fa-times', style={'marginRight': '8px'}),
            'Clear Selection'
        ],
        className='custom-dropdown-item',
        id={'type': 'rating-option', 'index': '__CLEAR__'},
        n_clicks=0,
        style={'borderBottom': '2px solid rgba(222, 181, 34, 0.3)', 'fontWeight': '500'})
    )
    # 評分選項
    options.append(html.Div('⭐⭐⭐⭐⭐ 4~5 Stars',
                            className='custom-dropdown-item',
                            id={'type': 'rating-option', 'index': '4-5'},
                            n_clicks=0))
    options.append(html.Div('⭐⭐⭐⭐ 3~4 Stars',
                            className='custom-dropdown-item',
                            id={'type': 'rating-option', 'index': '3-4'},
                            n_clicks=0))
    options.append(html.Div('⭐⭐⭐ 2~3 Stars',
                            className='custom-dropdown-item',
                            id={'type': 'rating-option', 'index': '2-3'},
                            n_clicks=0))
    options.append(html.Div('⭐⭐ 1~2 Stars',
                            className='custom-dropdown-item',
                            id={'type': 'rating-option', 'index': '1-2'},
                            n_clicks=0))
    return options

########################
#### UI Component Functions ####
########################

def create_primary_button(text, button_id=None, icon=None):
    """創建主要 CTA 按鈕"""
    children = []
    if icon:
        children.append(html.I(className=icon, style={'marginRight': '8px'}))
    children.append(text)

    return html.Button(
        children,
        id=button_id,
        className='btn-primary',
        n_clicks=0
    )

def create_destination_card(restaurant):
    """創建目的地卡片 (使用餐廳資料) - 可點擊並導航到詳細頁面"""
    card_content = html.Div([
        html.Img(
            src='/assets/food_dirtyrice.png',  # 使用相同圖片作為佔位符
            className='card-image'
        ),
        html.Div([
            html.Div(restaurant['Name'], className='card-title'),
            html.Div(restaurant.get('FirstCategory', 'Restaurant'), className='card-subtitle'),
            html.Div([
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.Span(f"{restaurant['TotalRating']:.1f}")
            ], className='card-rating')
        ], className='card-overlay')
    ], className='destination-card')

    # 包裝在可點擊的容器中，使用 pattern-matching ID
    return html.Div(
        card_content,
        id={'type': 'restaurant-card', 'index': restaurant['Restaurant_ID']},
        n_clicks=0,
        style={'cursor': 'pointer'}
    )

def create_saved_trip_card(trip_data):
    """創建已存行程卡片"""
    return html.Div([
        html.Img(
            src='/assets/food_dirtyrice.png',
            className='trip-card-image'
        ),
        html.Div([
            html.Div(trip_data['title'], className='trip-card-title'),
            html.Div(trip_data['description'], className='trip-card-description'),
            html.Div([
                html.Span([html.I(className='fas fa-calendar'), trip_data['duration']]),
                html.Span([html.I(className='fas fa-map-marker-alt'), trip_data['location']])
            ], className='trip-card-meta')
        ], className='trip-card-content')
    ], className='saved-trip-card')

def create_add_new_card(text="Start planning a new trip..."):
    """創建新增功能卡片"""
    return html.Div([
        html.Div([
            html.I(className='fas fa-plus')
        ], className='add-new-icon'),
        html.Div(text, className='add-new-text')
    ], className='add-new-card', id='add-new-trip-btn', n_clicks=0)

def create_compound_search_bar():
    """創建優化的複合式搜尋欄（帶即時建議和進階篩選）"""
    return html.Div([
        # Keyword search bar (separate row for full width)
        html.Div([
            html.Div([
                html.I(className='fas fa-search', style={'color': '#deb522', 'fontSize': '1.2rem'}),
                dcc.Input(
                    id='search-destination',
                    type='text',
                    placeholder='Search restaurants by name (English or Japanese)...',
                    className='search-input',
                    debounce=False,  # 即時搜尋
                    style={
                        'background': 'transparent',
                        'border': 'none',
                        'color': '#ffffff',
                        'fontSize': '0.95rem',
                        'width': '100%',
                        'outline': 'none',
                        'paddingLeft': '0.75rem'
                    }
                )
            ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'gap': '0.75rem'}),

            html.Button([
                html.I(className='fas fa-search', style={'marginRight': '8px'}),
                'Search'
            ], id='search-btn', className='search-btn', n_clicks=0)
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'backgroundColor': '#1a1a1a',
            'padding': '0.75rem 1.5rem',
            'borderRadius': '8px',
            'border': '1px solid #333',
            'marginBottom': '1rem',
            'gap': '1rem'
        }),

        # Filters and buttons row
        html.Div([
            html.Div([
                html.Div([
                    html.I(className='fas fa-utensils', id='cuisine-icon',
                           style={'cursor': 'pointer', 'color': '#deb522'}, n_clicks=0),
                    html.Span(id='cuisine-selected-text',
                             children='Cuisine Type',
                             style={'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'})
                ], id='cuisine-trigger', style={'display': 'flex', 'alignItems': 'center'}, n_clicks=0),

                # Hidden dropdown list
                html.Div([
                    html.Div(create_cuisine_options(),
                            style={'maxHeight': '300px', 'overflowY': 'auto'})
                ], id='cuisine-dropdown-menu', className='custom-dropdown-menu',
                   style={'display': 'none'})
            ], className='search-input-group', style={'flex': '1', 'minWidth': '200px', 'position': 'relative'}),

            html.Div([
                html.Div([
                    html.I(className='fas fa-star', id='rating-icon',
                           style={'cursor': 'pointer', 'color': '#deb522'}, n_clicks=0),
                    html.Span(id='rating-selected-text',
                             children='Rating',
                             style={'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'})
                ], id='rating-trigger', style={'display': 'flex', 'alignItems': 'center'}, n_clicks=0),

                # Hidden dropdown list
                html.Div([
                    html.Div(create_rating_options(),
                            style={'maxHeight': '300px', 'overflowY': 'auto'})
                ], id='rating-dropdown-menu', className='custom-dropdown-menu',
                   style={'display': 'none'})
            ], className='search-input-group', style={'flex': '1', 'minWidth': '200px', 'position': 'relative'}),

            # Advanced filters toggle button
            html.Button([
                html.I(className='fas fa-sliders-h', style={'marginRight': '8px'}),
                'Filters'
            ], id='toggle-advanced-filters', className='btn-secondary', n_clicks=0)
        ], className='search-container'),

        # Advanced filters panel (collapsible)
        html.Div([
            html.Div([
                # Price range filter
                html.Div([
                    html.Label('Price Range', style={'color': '#deb522', 'fontWeight': 'bold', 'marginBottom': '0.5rem'}),
                    dcc.RangeSlider(
                        id='price-range-filter',
                        min=0,
                        max=30000,
                        step=1000,
                        value=[0, 30000],
                        marks={
                            0: '¥0',
                            10000: '¥10K',
                            20000: '¥20K',
                            30000: '¥30K+'
                        },
                        tooltip={'placement': 'bottom', 'always_visible': False}
                    )
                ]),

                # Clear filters button
                html.Button([
                    html.I(className='fas fa-undo', style={'marginRight': '8px'}),
                    'Clear Filters'
                ], id='clear-filters-btn', className='btn-secondary', n_clicks=0, style={'marginTop': '1rem', 'width': '100%'})
            ], style={
                'backgroundColor': '#1a1a1a',
                'padding': '1.5rem',
                'borderRadius': '8px',
                'border': '1px solid #333',
                'marginTop': '1rem'
            })
        ], id='advanced-filters-panel', style={'display': 'none'})
    ], style={'width': '100%'})

##############################################
####  餐廳詳細頁面布局函數（Restaurant Detail Page）  ####
##############################################

def create_loading_state():
    """載入狀態顯示（Loading spinner）"""
    return html.Div([
        html.I(className='fas fa-spinner fa-spin',
               style={'fontSize': '3rem', 'color': '#deb522'}),
        html.P('Loading restaurant details...',
               style={'color': '#ffffff', 'marginTop': '1rem', 'fontSize': '1.2rem'})
    ], style={
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'minHeight': '80vh',
        'backgroundColor': '#1a1a1a'
    })

def create_error_state(error_message):
    """錯誤狀態顯示（Error display with back button）"""
    return html.Div([
        html.I(className='fas fa-exclamation-triangle',
               style={'fontSize': '3rem', 'color': '#deb522', 'marginBottom': '1rem'}),
        html.H2('Restaurant Not Found',
                style={'color': '#ffffff', 'marginBottom': '0.5rem'}),
        html.P(error_message,
               style={'color': '#888888', 'marginBottom': '2rem', 'fontSize': '1.1rem'}),
        html.Button([
            html.I(className='fas fa-arrow-left', style={'marginRight': '8px'}),
            'Back to Restaurants'
        ], id='error-back-btn', className='btn-primary', n_clicks=0)
    ], style={
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'minHeight': '80vh',
        'backgroundColor': '#1a1a1a',
        'textAlign': 'center',
        'padding': '2rem'
    })

def create_detail_header():
    """創建餐廳詳細頁面的頁首（包含返回按鈕和用戶下拉菜單）"""
    return html.Div([
        html.Div([
            # 返回按鈕
            html.Button([
                html.I(className='fas fa-arrow-left', style={'marginRight': '8px'}),
                'Back'
            ], id='restaurant-detail-back-btn', className='btn-secondary', n_clicks=0,
               style={'marginRight': 'auto'}),

            # 用戶頭像和下拉菜單（右側）
            html.Div([
                html.Div([
                    html.I(className='fas fa-user')
                ], id='user-avatar-detail', className='user-avatar', n_clicks=0),

                html.Div([
                    html.Div([
                        html.I(className='fas fa-user-circle'),
                        html.Span('Profile')
                    ], className='dropdown-item', id='menu-profile-detail', n_clicks=0),
                    html.Div([
                        html.I(className='fas fa-sign-out-alt'),
                        html.Span('Logout')
                    ], className='dropdown-item', id='menu-logout-detail', n_clicks=0)
                ], id='user-dropdown-detail', className='user-dropdown')
            ], style={'position': 'relative'}),

            # 下拉菜單狀態儲存
            dcc.Store(id='dropdown-open-detail', data=False, storage_type='memory')
        ], style={
            'maxWidth': '1400px',
            'margin': '0 auto',
            'padding': '1rem 2rem',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'space-between'
        })
    ], style={
        'backgroundColor': '#1a1a1a',
        'borderBottom': '1px solid #333',
        'position': 'sticky',
        'top': '0',
        'zIndex': '1000'
    })

def create_image_gallery():
    """創建圖片畫廊輪播組件（交叉淡入淡出效果）"""
    # Mujica文件夾中的圖片列表（使用前15張作為示例）
    gallery_images = [
        '/assets/Mujica/FB_IMG_1741782349578.jpg',
        '/assets/Mujica/FB_IMG_1741782457313.jpg',
        '/assets/Mujica/FB_IMG_1741782466354.jpg',
        '/assets/Mujica/FB_IMG_1741782481779.jpg',
        '/assets/Mujica/FB_IMG_1741782484895.jpg',
        '/assets/Mujica/FB_IMG_1741782486450.jpg',
        '/assets/Mujica/FB_IMG_1741782499553.jpg',
        '/assets/Mujica/FB_IMG_1741782505028.jpg',
        '/assets/Mujica/FB_IMG_1741782513961.jpg',
        '/assets/Mujica/FB_IMG_1741782525678.jpg',
        '/assets/Mujica/FB_IMG_1741782527528.jpg',
        '/assets/Mujica/FB_IMG_1741782530270.jpg',
        '/assets/Mujica/FB_IMG_1741782538112.jpg',
        '/assets/Mujica/FB_IMG_1741885757345.jpg',
        '/assets/Mujica/FB_IMG_1741885778449.jpg'
    ]

    return html.Div([
        # 圖片容器 - 雙層結構實現交叉淡入淡出
        html.Div([
            # 背景層（淡出的圖片）
            html.Div(
                id='gallery-image-bg',
                style={
                    'width': '100%',
                    'height': '100%',
                    'backgroundImage': f'url({gallery_images[0]})',
                    'backgroundSize': 'cover',
                    'backgroundPosition': 'center',
                    'position': 'absolute',
                    'top': '0',
                    'left': '0',
                    'transition': 'opacity 1.8s ease-in-out'
                }
            ),
            # 前景層（淡入的圖片）
            html.Div(
                id='gallery-image-fg',
                style={
                    'width': '100%',
                    'height': '100%',
                    'backgroundImage': f'url({gallery_images[0]})',
                    'backgroundSize': 'cover',
                    'backgroundPosition': 'center',
                    'position': 'absolute',
                    'top': '0',
                    'left': '0',
                    'opacity': '0',
                    'transition': 'opacity 1.8s ease-in-out',
                    'pointerEvents': 'none'
                }
            )
        ], style={
            'position': 'absolute',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'pointerEvents': 'none'  # 讓圖片不響應 hover
        }),

        # 左箭頭按鈕
        html.Button([
            html.I(className='fas fa-chevron-left')
        ], id='gallery-prev-btn', n_clicks=0, className='gallery-nav-btn gallery-prev'),

        # 右箭頭按鈕
        html.Button([
            html.I(className='fas fa-chevron-right')
        ], id='gallery-next-btn', n_clicks=0, className='gallery-nav-btn gallery-next'),

        # 圖片指示器（小圓點）
        html.Div([
            html.Div(
                className=f'gallery-indicator {"active" if i == 0 else ""}',
                id={'type': 'gallery-indicator', 'index': i},
                n_clicks=0
            ) for i in range(len(gallery_images))
        ], className='gallery-indicators'),

        # 自動播放定時器（每4秒切換一次）
        dcc.Interval(
            id='gallery-autoplay-interval',
            interval=4000,  # 4秒
            n_intervals=0
        ),

        # 存儲當前圖片索引和圖片列表
        dcc.Store(id='gallery-current-index', data=0),
        dcc.Store(id='gallery-images-list', data=gallery_images),
        # 存儲圖層切換狀態（用於交叉淡入淡出）
        dcc.Store(id='gallery-layer-toggle', data=False)
    ])

def create_detail_hero(data):
    """創建餐廳詳細頁面的 Hero 區域（大圖和主要資訊）"""
    # 生成星星評分
    rating = data.get('TotalRating', 0)
    full_stars = int(rating)
    stars = []
    for i in range(5):
        if i < full_stars:
            stars.append(html.I(className='fas fa-star', style={'color': '#deb522', 'marginRight': '4px'}))
        else:
            stars.append(html.I(className='far fa-star', style={'color': '#555555', 'marginRight': '4px'}))

    return html.Div([
        # 圖片畫廊（替換原本的單一圖片）
        create_image_gallery(),

        # 漸層遮罩
        html.Div(style={
            'position': 'absolute',
            'bottom': '0',
            'left': '0',
            'right': '0',
            'height': '70%',
            'background': 'linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.4) 70%, transparent 100%)',
            'pointerEvents': 'none'  # 讓遮罩不阻擋按鈕點擊
        }),

        # Hero 內容
        html.Div([
            html.H1(data.get('Name', 'Restaurant'), style={
                'color': '#ffffff',
                'fontSize': '3rem',
                'fontWeight': 'bold',
                'marginBottom': '0.5rem',
                'textShadow': '2px 2px 4px rgba(0,0,0,0.5)'
            }),
            html.Div(data.get('JapaneseName', ''), style={
                'color': '#cccccc',
                'fontSize': '1.5rem',
                'marginBottom': '1rem',
                'textShadow': '1px 1px 2px rgba(0,0,0,0.5)'
            }),
            html.Div([
                html.Div(stars + [
                    html.Span(f"{rating:.1f}", style={
                        'color': '#deb522',
                        'fontSize': '1.8rem',
                        'fontWeight': 'bold',
                        'marginLeft': '12px'
                    })
                ], style={'marginBottom': '1rem'}),
                html.Div([
                    html.Span([
                        html.I(className='fas fa-utensils', style={'marginRight': '6px'}),
                        data.get('SecondCategory', data.get('FirstCategory', 'Restaurant'))
                    ], style={
                        'backgroundColor': 'rgba(222, 181, 34, 0.2)',
                        'border': '1px solid #deb522',
                        'color': '#deb522',
                        'padding': '8px 16px',
                        'borderRadius': '20px',
                        'marginRight': '10px',
                        'fontSize': '1rem'
                    }),
                    html.Span([
                        html.I(className='fas fa-yen-sign', style={'marginRight': '6px'}),
                        data.get('Price_Category', 'N/A')
                    ], style={
                        'backgroundColor': 'rgba(222, 181, 34, 0.2)',
                        'border': '1px solid #deb522',
                        'color': '#deb522',
                        'padding': '8px 16px',
                        'borderRadius': '20px',
                        'marginRight': '10px',
                        'fontSize': '1rem'
                    }),
                    html.Span([
                        html.I(className='fas fa-comment', style={'marginRight': '6px'}),
                        f"{data.get('ReviewNum', 0)} reviews"
                    ], style={
                        'backgroundColor': 'rgba(222, 181, 34, 0.2)',
                        'border': '1px solid #deb522',
                        'color': '#deb522',
                        'padding': '8px 16px',
                        'borderRadius': '20px',
                        'fontSize': '1rem'
                    })
                ])
            ])
        ], style={
            'position': 'absolute',
            'bottom': '3rem',
            'left': '2rem',
            'right': '2rem',
            'maxWidth': '1400px',
            'margin': '0 auto',
            'pointerEvents': 'none'  # 讓文字不阻擋按鈕點擊
        })
    ], style={
        'position': 'relative',
        'height': '50vh',
        'minHeight': '400px',
        'overflow': 'hidden'
    })

def create_location_section(data):
    """創建地點資訊區域"""
    lat = data.get('Lat')
    long = data.get('Long')
    has_coords = lat is not None and long is not None

    return html.Div([
        html.H3('Location', style={'color': '#deb522', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div([
            html.I(className='fas fa-map-marker-alt', style={'color': '#deb522', 'marginRight': '12px', 'fontSize': '1.2rem'}),
            html.Span(data.get('Station', 'Not Available'), style={'color': '#ffffff', 'fontSize': '1.1rem'})
        ], style={'marginBottom': '1rem', 'display': 'flex', 'alignItems': 'center'}),
        html.Small(f"Coordinates: {lat:.6f}, {long:.6f}" if has_coords else "Coordinates not available",
                   style={'color': '#888888', 'fontSize': '0.9rem'})
    ], style={
        'backgroundColor': '#1a1a1a',
        'border': '1px solid #333',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem'
    })

def create_pricing_section(data):
    """創建價格資訊區域"""
    dinner_price = data.get('DinnerPrice', 'Not Available')
    lunch_price = data.get('LunchPrice', 'Not Available')

    return html.Div([
        html.H3('Pricing', style={'color': '#deb522', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div([
            html.I(className='fas fa-moon', style={'color': '#deb522', 'marginRight': '12px', 'fontSize': '1.1rem'}),
            html.Span('Dinner: ', style={'color': '#cccccc', 'marginRight': '8px', 'fontSize': '1rem'}),
            html.Span(dinner_price, style={'color': '#ffffff', 'fontSize': '1.1rem', 'fontWeight': '500'})
        ], style={'marginBottom': '0.8rem', 'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.I(className='fas fa-sun', style={'color': '#deb522', 'marginRight': '12px', 'fontSize': '1.1rem'}),
            html.Span('Lunch: ', style={'color': '#cccccc', 'marginRight': '8px', 'fontSize': '1rem'}),
            html.Span(lunch_price, style={'color': '#ffffff', 'fontSize': '1.1rem', 'fontWeight': '500'})
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={
        'backgroundColor': '#1a1a1a',
        'border': '1px solid #333',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem'
    })

def create_categories_section(data):
    """創建分類標籤區域"""
    first_category = data.get('FirstCategory', '')
    second_category = data.get('SecondCategory', '')

    categories = []
    if first_category:
        categories.append(html.Span(first_category, style={
            'backgroundColor': 'rgba(222, 181, 34, 0.1)',
            'border': '1px solid #deb522',
            'color': '#deb522',
            'padding': '8px 16px',
            'borderRadius': '20px',
            'marginRight': '10px',
            'fontSize': '1rem',
            'display': 'inline-block'
        }))
    if second_category and second_category != first_category:
        categories.append(html.Span(second_category, style={
            'backgroundColor': 'rgba(222, 181, 34, 0.1)',
            'border': '1px solid #deb522',
            'color': '#deb522',
            'padding': '8px 16px',
            'borderRadius': '20px',
            'fontSize': '1rem',
            'display': 'inline-block'
        }))

    if not categories:
        categories.append(html.Span('No categories available', style={'color': '#888888', 'fontSize': '1rem'}))

    return html.Div([
        html.H3('Categories', style={'color': '#deb522', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div(categories)
    ], style={
        'backgroundColor': '#1a1a1a',
        'border': '1px solid #333',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem'
    })

def create_map_placeholder_section(data):
    """創建 Google Maps 地圖區域（顯示餐廳位置和附近餐廳）"""
    # 獲取餐廳坐標
    lat = data.get('Lat')
    long = data.get('Long')
    restaurant_id = data.get('Restaurant_ID')
    restaurant_name = data.get('Name', 'Unknown')
    station = data.get('Station', 'Kyoto')

    # 如果沒有坐標，顯示佔位符
    if lat is None or long is None:
        return html.Div([
            html.H3('Map', style={'color': '#deb522', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
            html.Div([
                html.I(className='fas fa-map-marker-alt', style={'fontSize': '3rem', 'color': '#555555', 'marginBottom': '1rem'}),
                html.P('Location coordinates not available', style={'color': '#888888', 'fontSize': '1rem', 'textAlign': 'center'})
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'justifyContent': 'center',
                'minHeight': '200px'
            })
        ], style={
            'backgroundColor': '#1a1a1a',
            'border': '1px solid #333',
            'borderRadius': '12px',
            'padding': '1.5rem'
        })

    # 獲取附近餐廳
    nearby_restaurants = get_nearby_restaurants(lat, long, limit=5, exclude_id=restaurant_id)

    # 構建 Google Maps URL（包含多個標記）
    # 主餐廳標記（紅色，默認）
    markers_param = f"{lat},{long}"

    # 添加附近餐廳標記（使用不同顏色）
    for nearby in nearby_restaurants[:3]:  # 限制為3個附近餐廳以保持地圖清晰
        markers_param += f"|{nearby['Lat']},{nearby['Long']}"

    # Google Maps Embed URL（使用 place 模式顯示主餐廳）
    google_maps_url = f"https://www.google.com/maps?q={lat},{long}&z=15&output=embed"

    # 創建地圖 iframe
    map_component = html.Iframe(
        src=google_maps_url,
        style={
            'width': '100%',
            'height': '400px',
            'border': 'none',
            'borderRadius': '8px'
        }
    )

    # 創建附近餐廳列表
    nearby_cards = []
    for i, nearby in enumerate(nearby_restaurants, 1):
        # 格式化評分為小數點一位
        rating = nearby.get('TotalRating', 'N/A')
        if rating != 'N/A' and rating is not None:
            rating_display = f"{float(rating):.1f}"
        else:
            rating_display = 'N/A'

        card = html.Div([
            html.Div([
                html.Div(f"{i}", style={
                    'backgroundColor': '#3388ff',
                    'color': 'white',
                    'width': '24px',
                    'height': '24px',
                    'borderRadius': '50%',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'fontSize': '0.85rem',
                    'fontWeight': 'bold',
                    'marginRight': '12px',
                    'flexShrink': '0'
                }),
                html.Div([
                    html.Div(nearby['Name'], style={
                        'color': '#ffffff',
                        'fontSize': '0.95rem',
                        'fontWeight': '600',
                        'marginBottom': '4px'
                    }),
                    html.Div([
                        html.Span([
                            html.I(className='fas fa-star', style={'color': '#deb522', 'fontSize': '0.75rem', 'marginRight': '4px'}),
                            rating_display
                        ], style={'marginRight': '12px', 'fontSize': '0.85rem'}),
                        html.Span([
                            html.I(className='fas fa-map-marker-alt', style={'color': '#888', 'fontSize': '0.75rem', 'marginRight': '4px'}),
                            f"{nearby.get('distance', 0):.2f} km"
                        ], style={'fontSize': '0.85rem'})
                    ], style={'color': '#aaaaaa'})
                ], style={'flex': '1'})
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'padding': '12px',
                'backgroundColor': '#1a1a1a',
                'border': '1px solid #333',
                'borderRadius': '8px',
                'marginBottom': '8px',
                'transition': 'border-color 0.3s',
                'cursor': 'pointer'
            }, className='nearby-restaurant-card',
            id={'type': 'nearby-restaurant-card', 'index': nearby['Restaurant_ID']},
            n_clicks=0)
        ])
        nearby_cards.append(card)

    return html.Div([
        html.H3('Location & Map', style={'color': '#deb522', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div([
            html.I(className='fas fa-map-marker-alt', style={'color': '#deb522', 'marginRight': '8px'}),
            f"{station}, Kyoto"
        ], style={'color': '#cccccc', 'marginBottom': '1rem', 'fontSize': '0.95rem'}),

        # Google Map
        map_component,

        html.A(
            [
                html.I(className='fas fa-external-link-alt', style={'marginRight': '6px'}),
                'View on Google Maps'
            ],
            href=f"https://www.google.com/maps/search/?api=1&query={lat},{long}",
            target="_blank",
            style={
                'display': 'inline-block',
                'marginTop': '12px',
                'padding': '8px 16px',
                'backgroundColor': '#4285f4',
                'color': 'white',
                'textDecoration': 'none',
                'borderRadius': '6px',
                'fontSize': '0.9rem',
                'transition': 'background-color 0.3s'
            }
        ),

        # 附近餐廳列表
        html.Div([
            html.H4([
                html.I(className='fas fa-utensils', style={'marginRight': '8px', 'color': '#deb522'}),
                f'Nearby Restaurants ({len(nearby_restaurants)})'
            ], style={'color': '#ffffff', 'fontSize': '1.1rem', 'marginBottom': '1rem', 'marginTop': '2rem'}),
            html.Div(nearby_cards)
        ]) if nearby_restaurants else html.Div()

    ], style={
        'backgroundColor': '#1a1a1a',
        'border': '1px solid #333',
        'borderRadius': '12px',
        'padding': '1.5rem'
    })

def create_ratings_breakdown_section(data):
    """創建評分細節區域"""
    def create_rating_row(label, rating):
        """生成單個評分行"""
        if rating is None or pd.isna(rating):
            rating = 0.0

        full_stars = int(rating)
        stars = []
        for i in range(5):
            if i < full_stars:
                stars.append(html.I(className='fas fa-star', style={'color': '#deb522', 'marginRight': '3px', 'fontSize': '0.9rem'}))
            else:
                stars.append(html.I(className='far fa-star', style={'color': '#555555', 'marginRight': '3px', 'fontSize': '0.9rem'}))

        return html.Div([
            html.Span(label, style={'color': '#cccccc', 'minWidth': '80px', 'fontSize': '1rem'}),
            html.Div(stars, style={'display': 'flex', 'alignItems': 'center', 'flex': '1'}),
            html.Span(f"{rating:.1f}", style={'color': '#ffffff', 'fontWeight': 'bold', 'marginLeft': '12px', 'fontSize': '1.1rem'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '0.8rem'})

    return html.Div([
        html.H3('Ratings Breakdown', style={'color': '#deb522', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        create_rating_row('Overall', data.get('TotalRating', 0)),
        create_rating_row('Dinner', data.get('DinnerRating', 0)),
        create_rating_row('Lunch', data.get('LunchRating', 0))
    ], style={
        'backgroundColor': '#1a1a1a',
        'border': '1px solid #333',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem'
    })

def create_statistics_section(data):
    """創建統計資訊區域"""
    # Count actual reviews from the reviews list instead of using ReviewNum field
    reviews = data.get('reviews', []) if isinstance(data, dict) else []
    review_num = len(reviews)
    rating_category = data.get('Rating_Category', 'N/A')

    return html.Div([
        html.H3('Statistics', style={'color': '#deb522', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div([
            html.I(className='fas fa-comment', style={'color': '#deb522', 'marginRight': '12px', 'fontSize': '1.5rem'}),
            html.Div([
                html.Div(f"{review_num:,}", style={'color': '#ffffff', 'fontSize': '1.8rem', 'fontWeight': 'bold'}),
                html.Div('Total Reviews', style={'color': '#888888', 'fontSize': '0.9rem'})
            ])
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '1.5rem'}),
        html.Div([
            html.I(className='fas fa-award', style={'color': '#deb522', 'marginRight': '12px', 'fontSize': '1.5rem'}),
            html.Div([
                html.Div(rating_category, style={'color': '#ffffff', 'fontSize': '1.3rem', 'fontWeight': 'bold'}),
                html.Div('Rating Category', style={'color': '#888888', 'fontSize': '0.9rem'})
            ])
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={
        'backgroundColor': '#1a1a1a',
        'border': '1px solid #333',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem'
    })

def create_reviews_section(data):
    """創建評論區：包含星等分佈長條圖與點擊後顯示評論（含 Show all 按鈕）"""
    reviews = data.get('reviews', []) if isinstance(data, dict) else []
    # Build counts for 1..5
    counts = {i: 0 for i in range(1, 6)}
    for r in reviews:
        try:
            rating = r.get('rating', None)
            if rating is None:
                continue
            rating_int = int(round(float(rating)))
            if 1 <= rating_int <= 5:
                counts[rating_int] += 1
        except Exception:
            continue

    ratings = list(counts.keys())
    values = [counts[r] for r in ratings]

    # Create Plotly bar chart for visibility
    fig = px.bar(
        x=ratings,
        y=values,
        labels={'x': 'Stars', 'y': 'Count'},
        title='Ratings distribution',
        text=values,
        height=360
    )
    fig.update_traces(marker_color='#deb522', hovertemplate='Stars: %{x}<br>Count: %{y}<extra></extra>')
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title={'x':0.02, 'xanchor':'left', 'font': {'color':'#ffffff'}},
        xaxis=dict(tickfont=dict(color='#ffffff')),
        yaxis=dict(tickfont=dict(color='#ffffff')),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    comments_area = html.Div(id='reviews-comments', children=[
        html.Div('Click a star bar to show comments', style={'color': '#888888'})
    ], style={'marginTop': '1rem', 'color': '#ffffff', 'maxHeight': '260px', 'overflowY': 'auto'})

    return html.Div([
        html.H3('Reviews', style={'color': '#deb522', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        dcc.Graph(id='ratings-bar-chart', figure=fig, config={'displayModeBar': False}),
        comments_area
    ], style={
        'backgroundColor': '#1a1a1a',
        'border': '1px solid #333',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem'
    })

def create_restaurant_detail_page(restaurant_id):
    """創建餐廳詳細頁面（主函數）

    注意：這個函數返回頁面框架，實際數據由 callback 填充
    """
    return html.Div([
        # 頁首（返回按鈕和用戶菜單）
        create_detail_header(),

        # 主要內容容器（將由 callback 根據數據填充）
        html.Div(id='restaurant-detail-content', children=[
            create_loading_state()  # 預設顯示載入狀態
        ])
    ], style={'backgroundColor': '#1a1a1a', 'minHeight': '100vh'})

def create_restaurant_detail_content(data):
    """根據餐廳數據創建詳細頁面內容

    此函數由 callback 調用，用於填充實際數據
    """
    if not data:
        return create_loading_state()

    if 'error' in data:
        return create_error_state(data.get('error', 'An error occurred'))

    return html.Div([
        create_detail_hero(data),
        html.Div([
            html.Div([
                create_location_section(data),
                create_pricing_section(data),
                create_categories_section(data),
                create_map_placeholder_section(data)
            ], style={'flex': '1', 'minWidth': '300px'}),
            html.Div([
                create_ratings_breakdown_section(data),
                create_statistics_section(data),
                create_reviews_section(data)  # <-- use real reviews section
            ], style={'flex': '1', 'minWidth': '300px'})
        ], style={
            'maxWidth': '1400px',
            'margin': '0 auto',
            'padding': '3rem 2rem',
            'display': 'grid',
            'gridTemplateColumns': '1fr 1fr',
            'gap': '2rem'
        })
    ])

def create_hotel_card(hotel):
    """創建旅館卡片 (類似餐廳卡片)"""
    # 處理類型列表
    types_text = ', '.join(hotel['Types'][:2]) if isinstance(hotel['Types'], list) and hotel['Types'] else 'Hotel'
    
    card_content = html.Div([
        html.Img(
            src='/assets/food_dirtyrice.png',  # 可以替換為旅館圖片
            className='card-image'
        ),
        html.Div([
            html.Div(hotel['HotelName'], className='card-title'),
            html.Div(types_text, className='card-subtitle'),
            html.Div([
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.Span(f"{hotel['Rating']:.1f}")
            ], className='card-rating'),
            html.Div([
                html.I(className='fas fa-map-marker-alt', style={'marginRight': '5px', 'fontSize': '0.8rem'}),
                html.Span(hotel['Address'][:30] + '...' if len(hotel['Address']) > 30 else hotel['Address'],
                         style={'fontSize': '0.75rem', 'color': '#888'})
            ], style={'marginTop': '5px'})
        ], className='card-overlay')
    ], className='destination-card')
    
    return html.Div(
        card_content,
        id={'type': 'hotel-card', 'index': hotel['Hotel_ID']},
        n_clicks=0,
        style={'cursor': 'pointer'}
    )

def create_hotel_type_options():
    """創建旅館類型選項列表"""
    options = []
    
    # 清除選擇選項
    options.append(
        html.Div([
            html.I(className='fas fa-times', style={'marginRight': '8px'}),
            'Clear Selection'
        ],
        className='custom-dropdown-item',
        id={'type': 'hotel-type-option', 'index': '__CLEAR__'},
        n_clicks=0,
        style={'borderBottom': '2px solid rgba(222, 181, 34, 0.3)', 'fontWeight': '500'})
    )
    
    # 獲取所有旅館類型
    hotel_types = get_unique_hotel_types()
    
    for hotel_type in hotel_types:
        options.append(
            html.Div(hotel_type,
                    className='custom-dropdown-item',
                    id={'type': 'hotel-type-option', 'index': hotel_type},
                    n_clicks=0)
        )
    
    return options

def create_hotel_search_bar():
    """創建旅館搜尋欄 (類似餐廳搜尋)"""
    return html.Div([
        html.Div([
            html.Div([
                html.I(className='fas fa-search'),
                dcc.Input(
                    id='search-hotel',
                    type='text',
                    placeholder='Search hotels by name or location...',
                    className='search-input',
                    debounce=False
                )
            ], className='search-input-group', style={'position': 'relative', 'flex': '2'}),
            
            html.Div([
                html.Div([
                    html.I(className='fas fa-hotel', id='hotel-type-icon',
                           style={'cursor': 'pointer', 'color': '#deb522'}, n_clicks=0),
                    html.Span(id='hotel-type-selected-text',
                             children='Hotel Type',
                             style={'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'})
                ], id='hotel-type-trigger', style={'display': 'flex', 'alignItems': 'center'}, n_clicks=0),
                
                html.Div([
                    html.Div(create_hotel_type_options(),
                            style={'maxHeight': '300px', 'overflowY': 'auto'})
                ], id='hotel-type-dropdown-menu', className='custom-dropdown-menu',
                   style={'display': 'none'})
            ], className='search-input-group', style={'flex': '1.3', 'minWidth': '200px', 'position': 'relative'}),
            
            html.Button([
                html.I(className='fas fa-search', style={'marginRight': '8px'}),
                'Search'
            ], id='search-hotel-btn', className='search-btn', n_clicks=0)
        ], className='search-container')
    ], style={'width': '100%'})

def create_hotel_detail_page(hotel_id):
    """創建旅館詳情頁面框架 (包含 Header 和空的內容容器)"""
    return html.Div([
        # 頁首 (Header)
        html.Div([
            html.Div([
                # 返回按鈕
                html.Button([
                    html.I(className='fas fa-arrow-left', style={'marginRight': '8px'}),
                    'Back'
                ], id='hotel-detail-back-btn', className='btn-secondary', n_clicks=0,
                   style={'marginRight': 'auto'}),
                
                # 用戶頭像與選單
                html.Div([
                    html.Div([
                        html.I(className='fas fa-user')
                    ], id='user-avatar-hotel-detail', className='user-avatar', n_clicks=0),
                    
                    # 下拉選單
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-user-circle'),
                            html.Span('Profile')
                        ], className='dropdown-item', id='menu-profile-hotel-detail', n_clicks=0),
                        html.Div([
                            html.I(className='fas fa-sign-out-alt'),
                            html.Span('Logout')
                        ], className='dropdown-item', id='menu-logout-detail', n_clicks=0)
                    ], id='user-dropdown-detail', className='user-dropdown')
                ], style={'position': 'relative'}),

                # 下拉菜單狀態儲存
                dcc.Store(id='dropdown-open-detail', data=False, storage_type='memory')

            ], style={
                'maxWidth': '1400px',
                'margin': '0 auto',
                'padding': '1rem 2rem',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'space-between'
            })
        ], style={
            'backgroundColor': '#1a1a1a',
            'borderBottom': '1px solid #333',
            'position': 'sticky',
            'top': '0',
            'zIndex': '1000'
        }),
        
        # 主要內容容器 (將由 callback 填充 create_hotel_detail_content 的結果)
        html.Div(id='hotel-detail-content', children=[
            create_loading_state() # 預設顯示載入中
        ])
    ], style={'backgroundColor': '#1a1a1a', 'minHeight': '100vh'})

def create_hotel_detail_content(hotel_data):
    """根據旅館數據創建詳細頁面內容"""
    if not hotel_data:
        return create_loading_state()
    
    if 'error' in hotel_data:
        return create_error_state(hotel_data.get('error', 'An error occurred'))
    
    # 生成星星評分
    rating = hotel_data.get('Rating', 0)
    full_stars = int(rating)
    stars = []
    for i in range(5):
        if i < full_stars:
            stars.append(html.I(className='fas fa-star', style={'color': '#deb522', 'marginRight': '4px'}))
        else:
            stars.append(html.I(className='far fa-star', style={'color': '#555555', 'marginRight': '4px'}))
    
    # 處理類型列表
    types = hotel_data.get('Types', [])
    if isinstance(types, list):
        types_text = ', '.join(types)
    else:
        types_text = 'Hotel'
    
    return html.Div([
        # Hero 區域 (大圖)
        html.Div([
            html.Img(src='/assets/food_dirtyrice.png', style={
                'width': '100%',
                'height': '100%',
                'objectFit': 'cover',
                'position': 'absolute',
                'top': '0',
                'left': '0'
            }),
            html.Div(style={
                'position': 'absolute',
                'bottom': '0',
                'left': '0',
                'right': '0',
                'height': '70%',
                'background': 'linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.4) 70%, transparent 100%)'
            }),
            html.Div([
                html.H1(hotel_data.get('HotelName', 'Hotel'), style={
                    'color': '#ffffff',
                    'fontSize': '3rem',
                    'fontWeight': 'bold',
                    'marginBottom': '0.5rem',
                    'textShadow': '2px 2px 4px rgba(0,0,0,0.5)'
                }),
                html.Div([
                    html.Div(stars + [
                        html.Span(f"{rating:.1f}", style={
                            'color': '#deb522',
                            'fontSize': '1.8rem',
                            'fontWeight': 'bold',
                            'marginLeft': '12px'
                        })
                    ], style={'marginBottom': '1rem'}),
                    html.Div([
                        html.Span([
                            html.I(className='fas fa-hotel', style={'marginRight': '6px'}),
                            types_text
                        ], style={
                            'backgroundColor': 'rgba(222, 181, 34, 0.2)',
                            'border': '1px solid #deb522',
                            'color': '#deb522',
                            'padding': '8px 16px',
                            'borderRadius': '20px',
                            'marginRight': '10px',
                            'fontSize': '1rem'
                        }),
                        html.Span([
                            html.I(className='fas fa-comment', style={'marginRight': '6px'}),
                            f"{int(hotel_data.get('UserRatingsTotal', 0))} reviews"
                        ], style={
                            'backgroundColor': 'rgba(222, 181, 34, 0.2)',
                            'border': '1px solid #deb522',
                            'color': '#deb522',
                            'padding': '8px 16px',
                            'borderRadius': '20px',
                            'fontSize': '1rem'
                        })
                    ])
                ])
            ], style={
                'position': 'absolute',
                'bottom': '3rem',
                'left': '2rem',
                'right': '2rem',
                'maxWidth': '1400px',
                'margin': '0 auto'
            })
        ], style={
            'position': 'relative',
            'height': '50vh',
            'minHeight': '400px',
            'overflow': 'hidden'
        }),
        
        # --- 內容容器 (包含詳細資訊 Grid + 分析圖表) ---
        html.Div([
            # 1. 上半部：詳細資訊 Grid
            html.Div([
                html.Div([
                    # 左側：地址和地圖
                    html.Div([
                        html.Div([
                            html.H3('Location', style={'color': '#deb522', 'marginBottom': '1rem'}),
                            html.Div([
                                html.I(className='fas fa-map-marker-alt', style={'marginRight': '12px', 'color': '#deb522'}),
                                html.Span(hotel_data.get('Address', 'N/A'))
                            ], style={'color': '#ffffff', 'marginBottom': '1rem'}),
                            # Google Map
                            html.Iframe(
                                src=f"https://www.google.com/maps?q={hotel_data.get('Lat')},{hotel_data.get('Long')}&z=15&output=embed",
                                style={
                                    'width': '100%',
                                    'height': '300px',
                                    'border': 'none',
                                    'borderRadius': '8px',
                                    'marginTop': '1rem'
                                }
                            )
                        ], style={
                            'backgroundColor': '#1a1a1a',
                            'border': '1px solid #333',
                            'borderRadius': '12px',
                            'padding': '1.5rem',
                            'marginBottom': '1.5rem'
                        })
                    ], style={'flex': '1'}),
                    
                    # 右側：評分和附近旅館
                    html.Div([
                        create_reviews_section(hotel_data),
                        html.Div(id='nearby-hotels-section')
                    ], style={'flex': '1'})
                ], style={
                    'display': 'grid',
                    'gridTemplateColumns': '1fr 1fr',
                    'gap': '2rem',
                    'marginBottom': '2rem' # 增加底部間距，讓圖表不會黏太近
                }),

                # 2. 下半部：分析圖表 (放在這裡！)
                create_hotel_analytics_charts(hotel_data.get('Hotel_ID'))

            ])
        ], style={
            'maxWidth': '1400px',
            'margin': '0 auto',
            'padding': '3rem 2rem'
        })
    ])

def create_restaurant_map_chart():
    """Creates a mapbox scatter plot of all restaurants."""
    df = get_all_restaurants()
    # Filter out entries without coordinates
    df = df.dropna(subset=['Lat', 'Long'])

    # Create 'RatingCategory' based on 'TotalRating'
    bins = [0, 2, 3, 4, 5]
    labels = ['1-2 Stars', '2-3 Stars', '3-4 Stars', '4-5 Stars']
    df['RatingCategory'] = pd.cut(df['TotalRating'], bins=bins, labels=labels, right=False, include_lowest=True)

    # Ensure Restaurant_ID is integer
    df['Restaurant_ID_int'] = df['Restaurant_ID'].astype(int)

    fig = px.scatter_map(
        df,
        lat="Lat",
        lon="Long",
        hover_name="JapaneseName",
        hover_data={"TotalRating": ':.1f', "FirstCategory": True, "RatingCategory": True},
        color="RatingCategory",
        color_discrete_map={
            "1-2 Stars": "#FF6347",
            "2-3 Stars": "#FFA500",
            "3-4 Stars": "#FFD700",
            "4-5 Stars": "#32CD32"
        },
        zoom=11,
        center={"lat": 35.0116, "lon": 135.7681},
        height=600,
        map_style="carto-positron",
        custom_data=['Restaurant_ID_int', 'Name']  # Add Restaurant ID for click handling
    )
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=True,
        legend_title_text='Rating',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(0,0,0,0.5)',
            font=dict(
                color='white'
            )
        ),
        clickmode='event+select'  # Enable click events
    )
    # Update hover template to show it's clickable
    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>' +
                     'Rating: %{customdata[1]}<br>' +
                     '<i>Click to view details</i><extra></extra>'
    )
    return dcc.Graph(id='restaurant-map-graph', figure=fig)


def create_hotel_map_chart():
    """Creates a mapbox scatter plot of all hotels."""
    df = get_all_hotels()
    # Filter out entries without coordinates
    df = df.dropna(subset=['Lat', 'Long'])

    # Create 'RatingCategory' based on 'Rating'
    bins = [0, 2, 3, 4, 5]
    labels = ['1-2 Stars', '2-3 Stars', '3-4 Stars', '4-5 Stars']
    df['RatingCategory'] = pd.cut(df['Rating'], bins=bins, labels=labels, right=False, include_lowest=True)

    # Ensure Hotel_ID is integer
    df['Hotel_ID_int'] = df['Hotel_ID'].astype(int)

    fig = px.scatter_map(
        df,
        lat="Lat",
        lon="Long",
        hover_name="HotelName",
        hover_data={"Rating": ':.1f', "Types": True, "RatingCategory": True},
        color="RatingCategory",
        color_discrete_map={
            "1-2 Stars": "#FF6347",
            "2-3 Stars": "#FFA500",
            "3-4 Stars": "#FFD700",
            "4-5 Stars": "#32CD32"
        },
        zoom=11,
        center={"lat": 35.0116, "lon": 135.7681},
        height=600,
        map_style="carto-positron",
        custom_data=['Hotel_ID_int', 'HotelName']  # Add Hotel ID for click handling
    )
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=True,
        legend_title_text='Rating',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(0,0,0,0.5)',
            font=dict(
                color='white'
            )
        ),
        clickmode='event+select'  # Enable click events
    )
    # Update hover template to show it's clickable
    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>' +
                     'Hotel: %{customdata[1]}<br>' +
                     '<i>Click to view details</i><extra></extra>'
    )
    return dcc.Graph(id='hotel-map-graph', figure=fig)

# --- 新增這個輔助函式 ---
def create_help_section(index_id, button_text, explanation_content):
    """
    建立一個「說明按鈕」和「折疊內容」的組合 (用於 app.py)
    """
    return html.Div([
        dbc.Button(
            [html.I(className="fas fa-info-circle", style={'marginRight': '8px'}), button_text],
            id={'type': 'help-btn-detail', 'index': index_id}, # 注意：這裡的 type 跟 analytics_page 的不同，避免衝突
            className="btn-outline-info",
            size="sm",
            n_clicks=0,
            style={'marginBottom': '10px', 'borderColor': '#00cec9', 'color': '#00cec9'}
        ),
        dbc.Collapse(
            dbc.Card(
                dbc.CardBody(explanation_content),
                style={'backgroundColor': '#222', 'border': '1px solid #444', 'color': '#ddd', 'marginBottom': '15px'}
            ),
            id={'type': 'help-collapse-detail', 'index': index_id},
            is_open=False,
        ),
    ])

def create_hotel_analytics_charts(hotel_id):
    """建立旅館分析圖表 (營收與訂單狀態) - 含說明按鈕版"""
    
    # 1. 取得資料
    revenue_df = get_revenue_trend(hotel_id)
    status_df = get_occupancy_status(hotel_id)
    
    if revenue_df.empty or status_df.empty:
        return html.Div("No booking data available for this hotel.", style={'color': '#888', 'padding': '2rem'})

    # 2. 製作營收趨勢圖
    fig_revenue = px.area(
        revenue_df, x='Month', y='Revenue',
        title='Monthly Revenue Trend', markers=True
    )
    fig_revenue.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff', title_font_size=18,
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'),
        margin=dict(l=40, r=20, t=60, b=40)
    )
    fig_revenue.update_traces(line_color='#deb522', fillcolor='rgba(222, 181, 34, 0.2)')

    # 3. 製作訂單狀態圖
    fig_status = px.bar(
        status_df, x='Month', y='Count', color='status',
        title='Booking Status (Confirmed vs Cancelled)',
        barmode='stack',
        color_discrete_map={'Confirmed': '#4caf50', 'Cancelled': '#f44336'}
    )
    fig_status.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff', title_font_size=18,
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'),
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # --- 4. 定義解釋文案 ---
    help_rev = [
        html.H5("營收趨勢解讀", style={'color': '#deb522'}),
        html.P("此圖顯示該旅館過去一段時間的「總營收」變化。"),
        html.Ul([
            html.Li("高峰：通常代表旅遊旺季（如櫻花季、楓葉季）。"),
            html.Li("低谷：代表淡季，建議此時推出促銷活動。"),
            html.Li("資料來源：基於系統內的實際訂單金額 (Price Paid) 計算。")
        ])
    ]

    help_status = [
        html.H5("訂單健康度分析", style={'color': '#4caf50'}),
        html.P("顯示每個月的「實際入住」與「取消」比例。"),
        html.Ul([
            html.Li("綠色 (Confirmed)：實際帶來的有效客源。"),
            html.Li("紅色 (Cancelled)：被取消的訂單。若紅色比例過高，需檢查是否房價過高或競爭力不足。"),
            html.Li("監控重點：當紅色區塊異常變長時，需介入調查原因。")
        ])
    ]

    # 5. 回傳佈局 (加入說明按鈕 + 固定高度)
    return html.Div([
        html.H3('Analytics Dashboard', style={'color': '#deb522', 'marginTop': '2rem', 'marginBottom': '1rem', 'borderBottom': '1px solid #333', 'paddingBottom': '10px'}),
        
        html.Div([
            # 左圖：營收
            html.Div([
                create_help_section('rev-detail-help', 'About Revenue', help_rev),
                dcc.Graph(figure=fig_revenue, style={'height': '500px'})
            ], style={'flex': '1', 'minWidth': '400px', 'backgroundColor': '#1a1a1a', 'padding': '10px', 'borderRadius': '8px'}),
            
            # 右圖：狀態
            html.Div([
                create_help_section('status-detail-help', 'About Cancellations', help_status),
                dcc.Graph(figure=fig_status, style={'height': '500px'})
            ], style={'flex': '1', 'minWidth': '400px', 'backgroundColor': '#1a1a1a', 'padding': '10px', 'borderRadius': '8px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '2rem'})
    ])


##########################
####   初始化應用程式   ####
##########################
app = Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    '/assets/voyage_styles.css'
],
           title='柔成員的旅遊平台', suppress_callback_exceptions=True)
server = app.server

# ===== 版面配置 =====
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Store(id='current-user-data', storage_type='memory'),  # 當前使用者資料
    dcc.Store(id='page-mode', data='login', storage_type='memory'),  # 'login' 或 'register'
    dcc.Store(id='current-page', data='overview', storage_type='memory'),  # 記錄當前頁面
    dcc.Store(id='menu-open', data=False, storage_type='memory'),  # 記錄選單開關狀態
    dcc.Store(id='view-mode', data='home', storage_type='memory'),  # 'home' 或 'restaurant-list'
    dcc.Store(id='navigation-trigger', storage_type='memory'),  # 導航觸發器
    dcc.Store(id='search-cuisine', storage_type='memory'),  # 選中的料理類型
    dcc.Store(id='search-rating', storage_type='memory'),  # 選中的評分範圍
    dcc.Store(id='active-dropdown', storage_type='memory', data=None),  # 當前打開的下拉菜單 ('cuisine', 'rating', or None)
    dcc.Store(id='close-dropdowns-trigger', storage_type='memory'),  # 觸發關閉所有下拉菜單
    # 餐廳詳細頁面狀態管理
    dcc.Store(id='selected-restaurant-id', storage_type='memory'),  # 選中的餐廳 ID
    dcc.Store(id='previous-page-location', storage_type='memory'),  # 上一頁位置 (用於返回導航)
    dcc.Store(id='restaurant-detail-data', storage_type='memory'),  # 餐廳詳細資料
    # Stores for restaurant list page
    dcc.Store(id='search-results-store', storage_type='memory'),
    dcc.Store(id='current-page-store', data=1, storage_type='memory'),
    dcc.Store(id='search-params-store', storage_type='memory'),
    #新增旅館相關 Stores (3個)
    dcc.Store(id='search-hotel-type', storage_type='memory'),  # 👈 存儲選中的旅館類型
    dcc.Store(id='hotel-search-results-store', storage_type='memory'),  # 👈 存儲旅館搜尋結果
    dcc.Store(id='hotel-current-page-store', data=1, storage_type='memory'),  # 👈 存儲旅館列表分頁狀態
    dcc.Store(id='hotel-detail-data', storage_type='memory'),  # 旅館詳細資料（包含 reviews）
    dcc.Store(id='dropdown-open', data=False, storage_type='memory'),  # User dropdown state for homepage
    html.Div(id='scroll-trigger', style={'display': 'none'}),  # 隱藏的滾動觸發器
    html.Div(id='page-content', style={'minHeight': '100vh'})
], style={'backgroundColor': '#1a1a1a', 'minHeight': '100vh'})

# ===== Profile Page Layout =====
def create_profile_page(user_data):
    """創建使用者個人檔案頁面"""
    if not user_data:
        return html.Div([
            html.H2('Error: Unable to load user data', style={'color': 'white', 'textAlign': 'center', 'padding': '2rem'})
        ])

    # Format dates
    created_at = user_data.get('created_at', 'N/A')
    last_login = user_data.get('last_login', 'N/A')

    if created_at and created_at != 'N/A':
        try:
            created_dt = datetime.fromisoformat(created_at)
            created_at = created_dt.strftime('%B %d, %Y at %I:%M %p')
        except:
            pass

    if last_login and last_login != 'N/A':
        try:
            login_dt = datetime.fromisoformat(last_login)
            last_login = login_dt.strftime('%B %d, %Y at %I:%M %p')
        except:
            pass

    return html.Div([
        # Header with back button
        html.Div([
            html.Div([
                # Logo
                html.Div('Trip', className='header-logo'),

                # Right side: Back button + User Avatar
                html.Div([
                    # Back button styled like View All button
                    html.A([
                        html.I(className='fas fa-arrow-left'),
                        html.Span('Back')
                    ], className='view-all-link', id='back-from-profile', n_clicks=0, style={
                        'cursor': 'pointer',
                        'marginRight': '1.5rem'
                    }),

                    # User Avatar with Dropdown
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-user')
                        ], className='user-avatar', id='user-avatar-profile', n_clicks=0),

                        # Dropdown Menu
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-user-circle'),
                                html.Span('Profile')
                            ], className='dropdown-item', id='dropdown-profile-page', n_clicks=0),
                            html.Div([
                                html.I(className='fas fa-sign-out-alt'),
                                html.Span('Logout')
                            ], className='dropdown-item', id='menu-logout-profile', n_clicks=0),
                        ], id='user-dropdown-profile', className='user-dropdown')
                    ], style={'position': 'relative'})
                ], style={'display': 'flex', 'alignItems': 'center'})
            ], className='header-content')
        ], className='global-header'),

        # Profile Content
        html.Div([
            html.Div([
                # Page Title
                html.H1('My Profile', style={
                    'color': '#deb522',
                    'fontSize': '2.5rem',
                    'marginBottom': '2rem',
                    'textAlign': 'center'
                }),

                # Profile Card
                html.Div([
                    # User Avatar Icon
                    html.Div([
                        html.I(className='fas fa-user-circle', style={
                            'fontSize': '6rem',
                            'color': '#deb522'
                        })
                    ], style={'textAlign': 'center', 'marginBottom': '2rem'}),

                    # User Information
                    html.Div([
                        # Username
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-user', style={'marginRight': '0.5rem', 'color': '#deb522'}),
                                html.Span('Username:', style={'fontWeight': 'bold', 'color': '#deb522'})
                            ], style={'marginBottom': '0.5rem'}),
                            html.Div(user_data.get('username', 'N/A'), style={'fontSize': '1.2rem', 'color': 'white'})
                        ], style={'marginBottom': '1.5rem'}),

                        # Email
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-envelope', style={'marginRight': '0.5rem', 'color': '#deb522'}),
                                html.Span('Email:', style={'fontWeight': 'bold', 'color': '#deb522'})
                            ], style={'marginBottom': '0.5rem'}),
                            html.Div(user_data.get('email', 'Not provided'), style={'fontSize': '1.2rem', 'color': 'white'})
                        ], style={'marginBottom': '1.5rem'}),

                        # Account Created
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-calendar-plus', style={'marginRight': '0.5rem', 'color': '#deb522'}),
                                html.Span('Member Since:', style={'fontWeight': 'bold', 'color': '#deb522'})
                            ], style={'marginBottom': '0.5rem'}),
                            html.Div(created_at, style={'fontSize': '1.2rem', 'color': 'white'})
                        ], style={'marginBottom': '1.5rem'}),

                        # Last Login
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-clock', style={'marginRight': '0.5rem', 'color': '#deb522'}),
                                html.Span('Last Login:', style={'fontWeight': 'bold', 'color': '#deb522'})
                            ], style={'marginBottom': '0.5rem'}),
                            html.Div(last_login, style={'fontSize': '1.2rem', 'color': 'white'})
                        ], style={'marginBottom': '1.5rem'}),
                    ], style={'padding': '2rem'})
                ], style={
                    'backgroundColor': '#2a2a2a',
                    'borderRadius': '12px',
                    'padding': '2rem',
                    'maxWidth': '600px',
                    'margin': '0 auto',
                    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.3)'
                })
            ], style={
                'maxWidth': '1200px',
                'margin': '0 auto',
                'padding': '7rem 2rem 3rem 2rem'
            })
        ], style={'backgroundColor': '#1a1a1a', 'minHeight': '100vh'})
    ])

# 主應用布局（登入後顯示）
def create_main_layout():
    return html.Div([
        # ===== Global Header =====
        html.Div([
            html.Div([
                # Logo
                html.Div('Trip', className='header-logo'),

                # Navigation
                html.Div([
                    html.Div('Destinations', className='nav-link', id='nav-destinations', n_clicks=0),
                    html.Div('Trip Planner', className='nav-link', id='nav-planner', n_clicks=0),
                    html.Div('Analytics', className='nav-link', id='nav-analytics', n_clicks=0)
                ], className='header-nav'),

                # Actions
                html.Div([
                    create_primary_button('Create a Trip', button_id='create-trip-btn', icon='fas fa-plus'),

                    # User Avatar with Dropdown
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-user')
                        ], className='user-avatar', id='user-avatar', n_clicks=0),

                        # Dropdown Menu
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-user-circle'),
                                html.Span('Profile')
                            ], className='dropdown-item', id='dropdown-profile', n_clicks=0),
                            html.Div([
                                html.I(className='fas fa-sign-out-alt'),
                                html.Span('Logout')
                            ], className='dropdown-item', id='menu-logout', n_clicks=0),
                        ], id='user-dropdown', className='user-dropdown')
                    ], style={'position': 'relative'})
                ], className='header-actions')
            ], className='header-content')
        ], className='global-header'),

        # ===== Hero Section =====
        html.Div([
            html.Img(src='/assets/food_dirtyrice.png', className='hero-background'),
            html.Div(className='hero-overlay'),
            html.Div([
                html.H1('旅遊平台', className='hero-title'),
                html.P('自己設計想要的旅遊阿，底迪', className='hero-subtitle')
            ], className='hero-content')
        ], className='hero-section'),

        # ===== Restaurants Section (現有) =====
        html.Div([
            html.Div([
                html.H2('Restaurants You\'ll Love', className='section-title'),
                html.A(['View All', html.I(className='fas fa-arrow-right')], 
                      className='view-all-link', id='view-all-restaurants', n_clicks=0)
            ], className='section-header'),
            html.Div([
                html.Div(id='destinations-card-container', className='card-row')
            ], className='card-scroll-container')
        ], className='content-section'),
        
        # ===== Hotels Section (新增) =====
        html.Div([
            html.Div([
                html.H2('Hotels You\'ll Love', className='section-title'),
                html.A(['View All', html.I(className='fas fa-arrow-right')], 
                      className='view-all-link', id='view-all-hotels', n_clicks=0)
            ], className='section-header'),
            html.Div([
                html.Div(id='hotels-card-container', className='card-row')
            ], className='card-scroll-container')
        ], className='content-section'),
        
        # ===== Personalized Content Section - Your Saved Trips & Favorites =====
        html.Div([
            html.H2('Your Saved Trips & Favorites', className='section-title'),

            # Tab Navigation
            html.Div([
                html.Div('Saved Trips', id='tab-saved-trips', className='tab-item active', n_clicks=0),
                html.Div('Wishlisted Hotels', id='tab-wishlisted', className='tab-item', n_clicks=0),
                html.Div('Favorite Restaurants', id='tab-favorites', className='tab-item', n_clicks=0)
            ], className='tab-navigation'),

            # Tab Content
            html.Div(id='tab-content-container')
        ], className='content-section'),

        # ===== NEW: Map Section =====
        html.Div([
            html.H2('Distribution in Kyoto', className='section-title'),
            dcc.RadioItems(
                id='map-type-switch',
                options=[
                    {'label': 'Restaurants', 'value': 'restaurants'},
                    {'label': 'Hotels', 'value': 'hotels'},
                ],
                value='restaurants',
                labelStyle={'display': 'inline-block', 'margin': '0 10px'},
                style={'textAlign': 'center', 'color': 'white', 'marginBottom': '1rem'}
            ),
            html.Div(id='map-container', children=[create_restaurant_map_chart()])
        ], className='content-section')
    ], style={'backgroundColor': '#0a0a0a', 'minHeight': '100vh'})

# 餐廳列表頁面布局（獨立頁面）
def create_restaurant_list_page():
    return html.Div([
        # ===== Header with back button =====
        html.Div([
            html.Div([
                # Back button and title
                html.Div([
                    html.Button([
                        html.I(className='fas fa-arrow-left'),
                        html.Span('Back', style={'marginLeft': '8px'})
                    ], id={'type': 'back-btn', 'index': 'restaurant-list'}, className='btn-secondary', n_clicks=0),
                    html.H1('Restaurant Directory', style={
                        'color': '#deb522',
                        'marginLeft': '2rem',
                        'fontSize': '2rem',
                        'fontWeight': 'bold'
                    })
                ], style={'display': 'flex', 'alignItems': 'center'}),

                # User Avatar
                html.Div([
                    html.Div([
                        html.I(className='fas fa-user')
                    ], className='user-avatar', id='user-avatar-list', n_clicks=0),

                    # Dropdown Menu
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-user-circle'),
                            html.Span('Profile')
                        ], className='dropdown-item', id='dropdown-profile-list', n_clicks=0),
                        html.Div([
                            html.I(className='fas fa-sign-out-alt'),
                            html.Span('Logout')
                        ], className='dropdown-item', id='menu-logout-list', n_clicks=0),
                    ], id='user-dropdown-list', className='user-dropdown')
                ], style={'position': 'relative'})
            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'maxWidth': '1400px',
                'margin': '0 auto',
                'padding': '1.5rem 2rem'
            })
        ], style={
            'backgroundColor': '#1a1a1a',
            'borderBottom': '1px solid #333',
            'position': 'sticky',
            'top': '0',
            'zIndex': '1000'
        }),

        # Store for dropdown state
        dcc.Store(id='dropdown-open-list', data=False, storage_type='memory'),

        # ===== Search and Filter Section =====
        html.Div([
            html.Div([
                # Search bar
                create_compound_search_bar(),

                # Search stats
                html.Div(id='search-stats', style={
                    'color': '#888888',
                    'fontSize': '0.95rem',
                    'marginTop': '1rem'
                })
            ], style={
                'maxWidth': '1000px',
                'margin': '0 auto'
            })
        ], style={
            'backgroundColor': '#0a0a0a',
            'padding': '2rem',
            'borderBottom': '1px solid #222'
        }),

        # ===== Restaurant Grid =====
        html.Div([
            html.Div(id='restaurant-grid', className='restaurant-list-grid')
        ], style={
            'backgroundColor': '#0a0a0a',
            'padding': '2rem',
            'minHeight': '60vh'
        }),

        # ===== Pagination Controls =====
        html.Div(id='pagination-controls', style={
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center',
            'gap': '0.5rem',
            'padding': '2rem',
            'backgroundColor': '#0a0a0a'
        }),

    ], style={'backgroundColor': '#0a0a0a', 'minHeight': '100vh'})

def create_hotel_list_page():
    """創建旅館列表頁面（類似餐廳列表頁）"""
    return html.Div([
        # ===== Header with back button =====
        html.Div([
            html.Div([
                # Back button and title
                html.Div([
                    html.Button([
                        html.I(className='fas fa-arrow-left'),
                        html.Span('Back', style={'marginLeft': '8px'})
                    ], id={'type': 'back-btn', 'index': 'hotel-list'}, className='btn-secondary', n_clicks=0),
                    html.H1('Hotel Directory', style={
                        'color': '#deb522',
                        'marginLeft': '2rem',
                        'fontSize': '2rem',
                        'fontWeight': 'bold'
                    })
                ], style={'display': 'flex', 'alignItems': 'center'}),

                # User Avatar
                html.Div([
                    html.Div([
                        html.I(className='fas fa-user')
                    ], className='user-avatar', id='user-avatar-hotel-list', n_clicks=0),

                    # Dropdown Menu
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-user-circle'),
                            html.Span('Profile')
                        ], className='dropdown-item', id='dropdown-profile-hotel-list', n_clicks=0),
                        html.Div([
                            html.I(className='fas fa-sign-out-alt'),
                            html.Span('Logout')
                        ], className='dropdown-item', id='menu-logout-hotel-list', n_clicks=0),
                    ], id='user-dropdown-hotel-list', className='user-dropdown')
                ], style={'position': 'relative'})
            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'maxWidth': '1400px',
                'margin': '0 auto',
                'padding': '1.5rem 2rem'
            })
        ], style={
            'backgroundColor': '#1a1a1a',
            'borderBottom': '1px solid #333',
            'position': 'sticky',
            'top': '0',
            'zIndex': '1000'
        }),

        # Store for dropdown state
        dcc.Store(id='dropdown-open-hotel-list', data=False, storage_type='memory'),

        # ===== Search and Filter Section =====
        html.Div([
            html.Div([
                # Search bar
                create_hotel_search_bar(),

                # Search stats
                html.Div(id='hotel-search-stats', style={
                    'color': '#888888',
                    'fontSize': '0.95rem',
                    'marginTop': '1rem'
                })
            ], style={
                'maxWidth': '1000px',
                'margin': '0 auto'
            })
        ], style={
            'backgroundColor': '#0a0a0a',
            'padding': '2rem',
            'borderBottom': '1px solid #222'
        }),

        # ===== Hotel Grid =====
        html.Div([
            html.Div(id='hotel-grid', className='restaurant-list-grid')
        ], style={
            'backgroundColor': '#0a0a0a',
            'padding': '2rem',
            'minHeight': '60vh'
        }),

        # ===== Pagination Controls =====
        html.Div(id='hotel-pagination-controls', style={
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center',
            'gap': '0.5rem',
            'padding': '2rem',
            'backgroundColor': '#0a0a0a'
        })
    ], style={'backgroundColor': '#0a0a0a', 'minHeight': '100vh'})

# 創建分頁按鈕
def create_pagination_buttons(current_page, total_pages):
    """創建數字分頁按鈕 (1 2 3 4 5 ...)"""
    if total_pages == 0:
        return html.Div('No results', style={'color': '#888888'})

    buttons = []

    # Previous button
    buttons.append(
        html.Button(
            [html.I(className='fas fa-chevron-left')],
            id={'type': 'page-btn', 'index': 'prev'},
            disabled=current_page == 1,
            className='pagination-btn',
            n_clicks=0,
            style={
                'backgroundColor': '#1a1a1a' if current_page == 1 else '#333',
                'color': '#666' if current_page == 1 else '#deb522',
                'border': '1px solid #444',
                'padding': '0.5rem 1rem',
                'cursor': 'not-allowed' if current_page == 1 else 'pointer',
                'borderRadius': '4px'
            }
        )
    )

    # Page number buttons
    # Show up to 7 page numbers
    start_page = max(1, current_page - 3)
    end_page = min(total_pages, current_page + 3)

    # First page
    if start_page > 1:
        buttons.append(
            html.Button(
                '1',
                id={'type': 'page-btn', 'index': 1},
                className='pagination-btn',
                n_clicks=0,
                style={
                    'backgroundColor': '#333',
                    'color': '#deb522',
                    'border': '1px solid #444',
                    'padding': '0.5rem 1rem',
                    'cursor': 'pointer',
                    'borderRadius': '4px'
                }
            )
        )
        if start_page > 2:
            buttons.append(html.Span('...', style={'color': '#666', 'padding': '0 0.5rem'}))

    # Middle pages
    for page in range(start_page, end_page + 1):
        is_active = page == current_page
        buttons.append(
            html.Button(
                str(page),
                id={'type': 'page-btn', 'index': page},
                className='pagination-btn active' if is_active else 'pagination-btn',
                n_clicks=0,
                style={
                    'backgroundColor': '#deb522' if is_active else '#333',
                    'color': '#000' if is_active else '#deb522',
                    'border': '2px solid #deb522' if is_active else '1px solid #444',
                    'padding': '0.5rem 1rem',
                    'cursor': 'default' if is_active else 'pointer',
                    'borderRadius': '4px',
                    'fontWeight': 'bold' if is_active else 'normal'
                }
            )
        )

    # Last page
    if end_page < total_pages:
        if end_page < total_pages - 1:
            buttons.append(html.Span('...', style={'color': '#666', 'padding': '0 0.5rem'}))
        buttons.append(
            html.Button(
                str(total_pages),
                id={'type': 'page-btn', 'index': total_pages},
                className='pagination-btn',
                n_clicks=0,
                style={
                    'backgroundColor': '#333',
                    'color': '#deb522',
                    'border': '1px solid #444',
                    'padding': '0.5rem 1rem',
                    'cursor': 'pointer',
                    'borderRadius': '4px'
                }
            )
        )

    # Next button
    buttons.append(
        html.Button(
            [html.I(className='fas fa-chevron-right')],
            id={'type': 'page-btn', 'index': 'next'},
            disabled=current_page == total_pages,
            className='pagination-btn',
            n_clicks=0,
            style={
                'backgroundColor': '#1a1a1a' if current_page == total_pages else '#333',
                'color': '#666' if current_page == total_pages else '#deb522',
                'border': '1px solid #444',
                'padding': '0.5rem 1rem',
                'cursor': 'not-allowed' if current_page == total_pages else 'pointer',
                'borderRadius': '4px'
            }
        )
    )

    return buttons

# ====== 認證相關 Callbacks ======

# 頁面路由控制
@app.callback(
    [Output('page-content', 'children'),
     Output('page-mode', 'data')],
    [Input('url', 'pathname'),
     Input('session-store', 'data'),
     Input('page-mode', 'data'),
     Input('view-mode', 'data'),
     Input('selected-restaurant-id', 'data')],
    prevent_initial_call=False
)
def display_page(pathname, session_data, current_mode, view_mode, restaurant_id_data):
    """根據 session 狀態、view_mode 和 pathname 顯示對應頁面"""
    # 清理過期 sessions
    clean_expired_sessions()

    # 檢查 session
    if session_data and 'session_id' in session_data:
        user_id = get_session(session_data['session_id'])
        if user_id:
            # 已登入，根據 pathname 和 view_mode 顯示不同頁面

            # === 優先檢查 view_mode (用於從任何頁面導航) ===

            # 檢查個人檔案頁面
            if view_mode == 'profile':
                user_data = get_user_full_details(user_id)
                return create_profile_page(user_data), 'main'

            # 檢查旅館列表頁面
            elif view_mode == 'hotel-list':
                return create_hotel_list_page(), 'main'

            # 檢查分析頁面
            elif view_mode == 'analytics':
                return create_analytics_layout(analytics_df), 'main'

            # 檢查餐廳列表頁面
            elif view_mode == 'restaurant-list':
                return create_restaurant_list_page(), 'main'

            # === 然後檢查 pathname (用於 URL 路由) ===

            # 檢查是否為旅館詳細頁面路由
            elif pathname and pathname.startswith('/hotel/'):
                try:
                    hotel_id = int(pathname.split('/')[-1])
                    return create_hotel_detail_page(hotel_id), 'main'
                except (ValueError, IndexError):
                    # 無效的旅館 ID，重定向到首頁
                    return create_main_layout(), 'main'

            # 檢查是否為餐廳詳細頁面路由
            elif pathname and pathname.startswith('/restaurant/'):
                if restaurant_id_data and restaurant_id_data.get('id'):
                    return create_restaurant_detail_page(restaurant_id_data['id']), 'main'
                else:
                    return create_restaurant_list_page(), 'main'

            # 預設顯示首頁
            else:
                return create_main_layout(), 'main'

    # 未登入，根據當前模式顯示登入或註冊頁
    if current_mode == 'register':
        return create_register_layout(), 'register'

    return create_login_layout(), 'login'


# 切換到註冊頁面
@app.callback(
    Output('page-mode', 'data', allow_duplicate=True),
    [Input('register-link', 'n_clicks')],
    prevent_initial_call=True
)
def switch_to_register(n_clicks):
    """切換到註冊頁面"""
    if n_clicks:
        return 'register'
    raise PreventUpdate

# 切換回登入頁面
@app.callback(
    Output('page-mode', 'data', allow_duplicate=True),
    [Input('back-to-login-link', 'n_clicks')],
    prevent_initial_call=True
)
def switch_to_login(n_clicks):
    """切換回登入頁面"""
    if n_clicks:
        return 'login'
    raise PreventUpdate

# 登入處理
@app.callback(
    [Output('session-store', 'data'),
     Output('login-error-message', 'children')],
    [Input('login-button', 'n_clicks'),
     Input('login-username', 'n_submit'),  # Add n_submit for username field
     Input('login-password', 'n_submit')],  # Add n_submit for password field
    [State('login-username', 'value'),
     State('login-password', 'value'),
     State('login-remember', 'value')],
    prevent_initial_call=True
)
def login(n_clicks, username_n_submit, password_n_submit, username, password, remember):
    """處理使用者登入"""
    # 檢查是哪個輸入觸發了回調
    ctx = callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # 只有當登入按鈕被點擊，或者在使用者名稱/密碼字段中按下了 Enter 鍵時才執行登入邏輯
    if trigger_id not in ['login-button', 'login-username', 'login-password']:
        raise PreventUpdate
    # 移除使用者輸入的前後空白，再驗證（避免使用者多打空格造成比對失敗）
    if isinstance (username, str):
        username = username.strip()
    if isinstance(password, str):
        password = password.strip()
    # 驗證輸入
    if not username or not password:
        return no_update, dbc.Alert('請輸入使用者名稱和密碼', color='danger')

    # 驗證使用者
    user = verify_user(username, password)

    if user:
        # 登入成功，建立 session
        session_id = str(uuid.uuid4())
        user_id = user[0]

        # 根據「記住我」設定過期時間
        if remember:
            expires_at = datetime.now() + timedelta(days=30)
        else:
            expires_at = datetime.now() + timedelta(hours=2)

        create_session(user_id, session_id, expires_at)

        return {'session_id': session_id, 'user_id': user_id, 'username': user[1]}, None
    else:
        return no_update, dbc.Alert('使用者名稱或密碼錯誤', color='danger')

# 註冊處理
@app.callback(
    Output('register-message', 'children'),
    [Input('register-button', 'n_clicks')],
    [State('register-username', 'value'),
     State('register-email', 'value'),
     State('register-password', 'value'),
     State('register-password-confirm', 'value')],
    prevent_initial_call=True
)
def register(n_clicks, username, email, password, password_confirm):
    """處理使用者註冊"""
    if not n_clicks:
        raise PreventUpdate

    # 驗證輸入
    if not username or not password:
        return dbc.Alert('請輸入使用者名稱和密碼', color='danger')

    if len(password) < 6:
        return dbc.Alert('密碼至少需要 6 個字元', color='danger')

    if password != password_confirm:
        return dbc.Alert('兩次輸入的密碼不一致', color='danger')

    # 建立使用者
    success, message = create_user(username, password, email)

    if success:
        return dbc.Alert([
            html.P(message, style={'marginBottom': '10px'}),
            html.P('請返回登入頁面進行登入', style={'marginBottom': '0'})
        ], color='success')
    else:
        return dbc.Alert(message, color='danger')

# ====== Navigation Callbacks ======

# Navigate to restaurant list page (from home page button)
@app.callback(
    Output('view-mode', 'data'),
    [Input('view-all-restaurants', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_to_restaurant_list(n_clicks):
    """導航到餐廳列表頁面"""
    if n_clicks:
        return 'restaurant-list'
    raise PreventUpdate

# Update navigation trigger when back button is clicked
@app.callback(
    Output('navigation-trigger', 'data'),
    [Input({'type': 'back-btn', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def trigger_back_navigation(n_clicks_list):
    """當返回按鈕被點擊時觸發導航"""
    if any(n_clicks_list):
        return 'home'
    raise PreventUpdate

# Listen to navigation trigger and update view-mode
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('navigation-trigger', 'data')],
    prevent_initial_call=True
)
def handle_navigation_trigger(nav_command):
    """根據導航觸發器更新視圖模式"""
    if nav_command:
        return nav_command
    raise PreventUpdate

# ====== Modern Homepage Callbacks ======

# Toggle user dropdown menu
@app.callback(
    [Output('user-dropdown', 'className'),
     Output('dropdown-open', 'data')],
    [Input('user-avatar', 'n_clicks')],
    [State('dropdown-open', 'data')],
    prevent_initial_call=True
)
def toggle_user_dropdown(n_clicks, is_open):
    """切換使用者下拉選單"""
    if n_clicks:
        new_state = not is_open
        className = 'user-dropdown show' if new_state else 'user-dropdown'
        return className, new_state
    raise PreventUpdate

# Handle logout from dropdown
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_dropdown(n_clicks, session_data):
    """從下拉選單登出"""
    if not n_clicks:
        raise PreventUpdate

    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])

    return None

# ====== Populate Destinations Cards ======

# ====== Modern Homepage Callbacks (Content Population) ======

# Populate Destinations/Restaurants Cards
@app.callback(
    Output('destinations-card-container', 'children'),
    [Input('url', 'pathname')]
)
def populate_destinations_cards(pathname):
    """填充餐廳卡片（橫向滾動）"""
    # Get random 4-5 star restaurants
    top_restaurants = get_random_top_restaurants(4)

    cards = []
    for _, restaurant in top_restaurants.iterrows():
        card = create_destination_card(restaurant)
        cards.append(card)

    return cards

@app.callback(
    Output('hotels-card-container', 'children'),
    [Input('url', 'pathname')]
)
def populate_hotels_cards(pathname):
    """填充旅館卡片（橫向滾動）"""
    top_hotels = get_random_top_hotels(4, min_rating=4.0)
    
    if len(top_hotels) > 0:
        cards = [create_hotel_card(row) for _, row in top_hotels.iterrows()]
        return cards
    else:
        return [html.Div("No hotels found", style={'color': '#888', 'padding': '2rem'})]

@app.callback(
    Output('hotels-card-container', 'children', allow_duplicate=True),
    [Input('search-hotel-btn', 'n_clicks'),
     Input('search-hotel-type', 'data')],
    [State('search-hotel', 'value')],
    prevent_initial_call=True
)
def handle_hotel_search(n_clicks, hotel_type, keyword):
    """處理旅館搜尋（主頁預覽）"""
    filtered_hotels = search_hotels(
        keyword=keyword,
        hotel_type=hotel_type,
        sort_by='rating_desc'
    )
    
    if len(filtered_hotels) > 0:
        preview = filtered_hotels.head(10)
        cards = [create_hotel_card(row) for _, row in preview.iterrows()]
        return cards
    else:
        return [html.Div([
            html.I(className='fas fa-hotel', style={'fontSize': '3rem', 'color': '#deb522', 'marginBottom': '1rem'}),
            html.H3('No hotels found', style={'color': '#ffffff'}),
            html.P('Try adjusting your search criteria', style={'color': '#888888'})
        ], style={'textAlign': 'center', 'padding': '4rem', 'width': '100%'})]
    
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('view-all-hotels', 'n_clicks')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def view_all_hotels(n_clicks, current_view):
    if n_clicks and current_view != 'hotel-list':
        return 'hotel-list'
    raise PreventUpdate

@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('nav-analytics', 'n_clicks')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def view_analytics(n_clicks, current_view):
    if n_clicks and current_view != 'analytics':
        return 'analytics'
    raise PreventUpdate


# Handle Tab Navigation
@app.callback(
    [Output('tab-saved-trips', 'className'),
     Output('tab-wishlisted', 'className'),
     Output('tab-favorites', 'className'),
     Output('tab-content-container', 'children')],
    [Input('tab-saved-trips', 'n_clicks'),
     Input('tab-wishlisted', 'n_clicks'),
     Input('tab-favorites', 'n_clicks')],
    prevent_initial_call=False
)
def handle_tab_navigation(saved_clicks, wishlisted_clicks, favorites_clicks):
    """處理標籤頁導航"""
    ctx = callback_context

    # Default to saved trips
    active_tab = 'saved-trips'

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'tab-wishlisted':
            active_tab = 'wishlisted'
        elif button_id == 'tab-favorites':
            active_tab = 'favorites'

    # Set active classes
    base_class = 'tab-item'
    active_class = 'tab-item active'

    tab_classes = (
        active_class if active_tab == 'saved-trips' else base_class,
        active_class if active_tab == 'wishlisted' else base_class,
        active_class if active_tab == 'favorites' else base_class
    )

    # Generate content based on active tab
    if active_tab == 'saved-trips':
        # Sample trip data
        trips = [
            {'title': 'Kyoto Cultural Journey', 'description': 'Experience traditional Japanese culture', 'duration': '7 Days', 'location': 'Kyoto, Japan'},
            {'title': 'Tokyo Food Adventure', 'description': 'Taste the best of Tokyo cuisine', 'duration': '5 Days', 'location': 'Tokyo, Japan'},
        ]

        cards = [create_saved_trip_card(trip) for trip in trips]
        cards.append(create_add_new_card("Start planning a new trip..."))

        content = html.Div(cards, className='card-row')
        content = html.Div(content, className='card-scroll-container')

    elif active_tab == 'wishlisted':
        content = html.Div([
            html.P('No wishlisted hotels yet. Start exploring!',
                   style={'color': '#888888', 'fontSize': '1.1rem', 'textAlign': 'center', 'padding': '3rem'})
        ])

    else:  # favorites
        # Show favorite restaurants
        fav_restaurants = get_random_top_restaurants(6)
        cards = []
        for _, restaurant in fav_restaurants.iterrows():
            card = create_saved_trip_card({
                'title': restaurant['Name'],
                'description': f"{restaurant['FirstCategory']} - {restaurant['SecondCategory']}",
                'duration': f"{restaurant['TotalRating']:.1f} ⭐",
                'location': restaurant['Station']
            })
            cards.append(card)

        content = html.Div(cards, className='card-grid')

    return (*tab_classes, content)

# Enhanced search function with advanced filters (使用數據庫查詢)
def search_restaurants(keyword=None, cuisine=None, rating=None, price_range=None,
                      min_reviews=None, stations=None, sort_by='rating_desc'):
    """
    進階餐廳搜尋功能（使用 SQL 數據庫查詢，替代 pandas 篩選）
    - keyword: 僅搜尋餐廳名稱（英文或日文）
    - cuisine: 精確匹配料理類型
    - rating: 評分範圍（例如 "4-5"）
    - price_range: 價格範圍 [min, max]
    - min_reviews: 最少評論數
    - stations: 車站列表（多選）
    - sort_by: 排序方式
    """
    # 使用數據庫查詢函數（從 utils/database.py）
    return db_search_restaurants(
        keyword=keyword,
        cuisine=cuisine,
        rating=rating,
        price_range=price_range,
        min_reviews=min_reviews,
        stations=stations,
        sort_by=sort_by
    )

# Get search suggestions based on keyword (優化使用數據庫查詢)
def get_search_suggestions(keyword, max_results=8):
    """
    根據關鍵字生成搜尋建議（使用數據庫查詢以提高性能）
    僅返回餐廳名稱的匹配結果
    """
    if not keyword or len(keyword.strip()) < 2:
        return []

    # 使用數據庫查詢獲取匹配的餐廳
    # 這比 pandas 篩選更快
    matched_restaurants = db_search_restaurants(keyword=keyword, sort_by='rating_desc')

    suggestions = []

    # 從結果中提取建議（僅顯示餐廳名稱）
    if len(matched_restaurants) > 0:
        # 餐廳名稱建議（顯示英文名和日文名）
        for _, row in matched_restaurants.head(max_results).iterrows():
            # 顯示英文名稱和日文名稱
            label = row['Name']
            if row.get('JapaneseName') and row['JapaneseName'].strip():
                label = f"{row['Name']} ({row['JapaneseName']})"

            suggestions.append({
                'type': 'restaurant',
                'value': row['Name'],
                'label': label,
                'icon': 'fa-utensils'
            })

    return suggestions[:max_results]

# ====== Search Enhancement Callbacks ======

# Search suggestions removed - users can directly search by restaurant name

# Toggle advanced filters panel
@app.callback(
    Output('advanced-filters-panel', 'style'),
    [Input('toggle-advanced-filters', 'n_clicks')],
    [State('advanced-filters-panel', 'style')],
    prevent_initial_call=True
)
def toggle_advanced_filters(n_clicks, current_style):
    """切換進階篩選面板"""
    if n_clicks:
        if current_style and current_style.get('display') == 'block':
            return {'display': 'none'}
        else:
            return {'display': 'block'}
    raise PreventUpdate

# Clear all filters
@app.callback(
    [Output('search-destination', 'value'),
     Output('search-cuisine', 'data', allow_duplicate=True),
     Output('search-rating', 'data', allow_duplicate=True),
     Output('price-range-filter', 'value'),
     Output('cuisine-selected-text', 'children', allow_duplicate=True),
     Output('cuisine-selected-text', 'style', allow_duplicate=True),
     Output('rating-selected-text', 'children', allow_duplicate=True),
     Output('rating-selected-text', 'style', allow_duplicate=True)],
    [Input('clear-filters-btn', 'n_clicks')],
    prevent_initial_call=True
)
def clear_all_filters(n_clicks):
    """清除所有篩選器"""
    if n_clicks:
        return (
            '', None, None, [0, 30000],
            'Cuisine Type', {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'},
            'Rating', {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'}
        )
    raise PreventUpdate

# Toggle cuisine dropdown menu with mutual exclusivity
@app.callback(
    [Output('cuisine-dropdown-menu', 'style'),
     Output('rating-dropdown-menu', 'style', allow_duplicate=True),
     Output('active-dropdown', 'data', allow_duplicate=True)],
    [Input('cuisine-trigger', 'n_clicks'),
     Input('cuisine-icon', 'n_clicks')],
    [State('active-dropdown', 'data')],
    prevent_initial_call=True
)
def toggle_cuisine_menu(trigger_clicks, icon_clicks, active_dropdown):
    """切換料理類型下拉菜單，並確保評分菜單關閉（互斥性）"""
    # 檢查是否真的有點擊事件（防止初始化觸發）
    if not trigger_clicks and not icon_clicks:
        raise PreventUpdate

    # 如果 cuisine 已經是活動狀態，則關閉它
    if active_dropdown == 'cuisine':
        return (
            {'display': 'none'},    # 關閉 cuisine
            {'display': 'none'},    # 保持 rating 關閉
            None                     # 沒有活動的下拉菜單
        )
    else:
        # 打開 cuisine，關閉 rating
        return (
            {'display': 'block'},   # 打開 cuisine
            {'display': 'none'},    # 關閉 rating
            'cuisine'               # 設置 cuisine 為活動狀態
        )

# Toggle rating dropdown menu with mutual exclusivity
@app.callback(
    [Output('cuisine-dropdown-menu', 'style', allow_duplicate=True),
     Output('rating-dropdown-menu', 'style', allow_duplicate=True),
     Output('active-dropdown', 'data', allow_duplicate=True)],
    [Input('rating-trigger', 'n_clicks'),
     Input('rating-icon', 'n_clicks')],
    [State('active-dropdown', 'data')],
    prevent_initial_call=True
)
def toggle_rating_menu(trigger_clicks, icon_clicks, active_dropdown):
    """切換評分下拉菜單，並確保料理類型菜單關閉（互斥性）"""
    # 檢查是否真的有點擊事件（防止初始化觸發）
    if not trigger_clicks and not icon_clicks:
        raise PreventUpdate

    # 如果 rating 已經是活動狀態，則關閉它
    if active_dropdown == 'rating':
        return (
            {'display': 'none'},    # 保持 cuisine 關閉
            {'display': 'none'},    # 關閉 rating
            None                     # 沒有活動的下拉菜單
        )
    else:
        # 打開 rating，關閉 cuisine
        return (
            {'display': 'none'},    # 關閉 cuisine
            {'display': 'block'},   # 打開 rating
            'rating'                # 設置 rating 為活動狀態
        )

# Handle cuisine option selection
@app.callback(
    [Output('search-cuisine', 'data', allow_duplicate=True),
     Output('cuisine-selected-text', 'children', allow_duplicate=True),
     Output('cuisine-selected-text', 'style', allow_duplicate=True),
     Output('cuisine-dropdown-menu', 'style', allow_duplicate=True),
     Output('active-dropdown', 'data', allow_duplicate=True)],
    [Input({'type': 'cuisine-option', 'index': ALL}, 'n_clicks')],
    [State({'type': 'cuisine-option', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def select_cuisine_option(n_clicks_list, option_ids):
    """選擇料理類型選項"""
    if not any(n_clicks_list):
        raise PreventUpdate

    # Use callback_context to find which option was actually clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Get the triggered input ID
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # Parse the JSON string to get the index
    triggered_dict = json.loads(triggered_id)
    selected_value = triggered_dict['index']

    # 處理清除選擇
    if selected_value == '__CLEAR__':
        return (
            None,  # 清除選擇
            'Cuisine Type',  # 重置顯示文本
            {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'},  # 重置為灰色
            {'display': 'none'},
            None  # 重置 active-dropdown
        )

    selected_label = remove_parentheses(selected_value)

    return (
        selected_value,
        selected_label,
        {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#ffffff'},
        {'display': 'none'},
        None  # 重置 active-dropdown
    )

# Handle rating option selection
@app.callback(
    [Output('search-rating', 'data', allow_duplicate=True),
     Output('rating-selected-text', 'children', allow_duplicate=True),
     Output('rating-selected-text', 'style', allow_duplicate=True),
     Output('rating-dropdown-menu', 'style', allow_duplicate=True),
     Output('active-dropdown', 'data', allow_duplicate=True)],
    [Input({'type': 'rating-option', 'index': ALL}, 'n_clicks')],
    [State({'type': 'rating-option', 'index': ALL}, 'id'),
     State({'type': 'rating-option', 'index': ALL}, 'children')],
    prevent_initial_call=True
)
def select_rating_option(n_clicks_list, option_ids, option_labels):
    """選擇評分選項"""
    if not any(n_clicks_list):
        raise PreventUpdate

    # Use callback_context to find which option was actually clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Get the triggered input ID
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # Parse the JSON string to get the index
    triggered_dict = json.loads(triggered_id)
    selected_value = triggered_dict['index']

    # 處理清除選擇
    if selected_value == '__CLEAR__':
        return (
            None,  # 清除選擇
            'Rating',  # 重置顯示文本
            {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'},  # 重置為灰色
            {'display': 'none'},
            None  # 重置 active-dropdown
        )

    # Find the label for this value
    selected_label = selected_value  # Default to value if not found
    for i, opt_id in enumerate(option_ids):
        if opt_id['index'] == selected_value:
            selected_label = option_labels[i]
            break

    return (
        selected_value,
        selected_label,
        {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#ffffff'},
        {'display': 'none'},
        None  # 重置 active-dropdown
    )

# Active filter chips removed - users can see filters in the filter panel

# Navigate to restaurant list when searching from homepage
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('search-btn', 'n_clicks'),
     Input('search-cuisine', 'data'),
     Input('search-rating', 'data')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def navigate_to_search_results(n_clicks, cuisine, rating, current_view_mode):
    """Navigate to restaurant list page when searching from homepage"""
    # Only navigate if currently on homepage
    if current_view_mode == 'home':
        return 'restaurant-list'
    raise PreventUpdate

# Toggle hotel type dropdown menu
@app.callback(
    [Output('hotel-type-dropdown-menu', 'style'),
     Output('active-dropdown', 'data', allow_duplicate=True)],
    [Input('hotel-type-trigger', 'n_clicks'),
     Input('hotel-type-icon', 'n_clicks')],
    [State('active-dropdown', 'data')],
    prevent_initial_call=True
)
def toggle_hotel_type_menu(trigger_clicks, icon_clicks, active_dropdown):
    """切換旅館類型下拉菜單"""
    if not trigger_clicks and not icon_clicks:
        raise PreventUpdate
    
    if active_dropdown == 'hotel-type':
        return {'display': 'none'}, None
    else:
        return {'display': 'block'}, 'hotel-type'

# Handle hotel type selection
@app.callback(
    [Output('search-hotel-type', 'data'),
     Output('hotel-type-selected-text', 'children'),
     Output('hotel-type-selected-text', 'style'),
     Output('hotel-type-dropdown-menu', 'style', allow_duplicate=True),
     Output('active-dropdown', 'data', allow_duplicate=True)],
    [Input({'type': 'hotel-type-option', 'index': ALL}, 'n_clicks')],
    [State({'type': 'hotel-type-option', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def select_hotel_type_option(n_clicks_list, option_ids):
    """選擇旅館類型選項"""
    if not any(n_clicks_list):
        raise PreventUpdate
    
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_dict = json.loads(triggered_id)
    selected_value = triggered_dict['index']
    
    if selected_value == '__CLEAR__':
        return (None, 'Hotel Type',
                {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'},
                {'display': 'none'}, None)
    
    return (selected_value, selected_value,
            {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#ffffff'},
            {'display': 'none'}, None)

# ====== Restaurant List Page Callbacks ======

# Handle search in restaurant list page with advanced filters
# 自动搜索：当选择料理类型、评分或价格范围时自动触发搜索
@app.callback(
    [Output('search-results-store', 'data'),
     Output('current-page-store', 'data', allow_duplicate=True),
     Output('search-params-store', 'data')],
    [Input('search-btn', 'n_clicks'),
     Input('search-cuisine', 'data'),
     Input('search-rating', 'data'),
     Input('price-range-filter', 'value')],
    [State('search-destination', 'value'),
     State('view-mode', 'data')],
    prevent_initial_call=True
)
def handle_restaurant_list_search(n_clicks, cuisine, rating, price_range, destination, view_mode):
    """處理餐廳列表頁的搜尋，並將結果存儲到 dcc.Store"""
    # 只有在列表頁面模式才觸發
    if view_mode != 'restaurant-list':
        raise PreventUpdate

    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if not triggered_id:
        raise PreventUpdate

    # Use enhanced search function with filters
    filtered_df = search_restaurants(
        keyword=destination,
        cuisine=cuisine,
        rating=rating,
        price_range=price_range,
        min_reviews=None,
        stations=None,
        sort_by='rating_desc'
    )

    # Store search results and parameters
    search_results = filtered_df.to_dict('records') if len(filtered_df) > 0 else []
    search_params = {
        'destination': destination,
        'cuisine': cuisine,
        'rating': rating,
        'price_range': price_range
    }

    # 返回結果，重置到第一頁
    return search_results, 1, search_params

# Update restaurant grid and pagination based on current page
@app.callback(
    [Output('restaurant-grid', 'children'),
     Output('pagination-controls', 'children'),
     Output('search-stats', 'children')],
    [Input('search-results-store', 'data'),
     Input('current-page-store', 'data')],
    prevent_initial_call=False
)
def update_restaurant_grid(search_results, current_page):
    """更新餐廳網格和分頁控制"""
    if search_results is None:
        # Initial load, fetch default results
        df = search_restaurants(sort_by='rating_desc')
        search_results = df.to_dict('records')

    if not search_results:
        return (
            html.Div([
                html.I(className='fas fa-utensils',
                      style={'fontSize': '4rem', 'color': '#deb522', 'marginBottom': '2rem'}),
                html.H3('No restaurants found', style={'color': '#ffffff', 'marginBottom': '1rem'}),
                html.P('Try adjusting your search criteria', style={'color': '#888888'})
            ], style={'textAlign': 'center', 'padding': '4rem'}),
            html.Div(),
            ''
        )

    # Pagination logic
    items_per_page = 15
    total_items = len(search_results)
    total_pages = (total_items + items_per_page - 1) // items_per_page

    # Get current page items
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_items = search_results[start_idx:end_idx]

    # Create restaurant cards in grid layout
    cards = []
    for restaurant in current_items:
        # 卡片內容
        card_content = html.Div([
            html.Img(
                src='/assets/food_dirtyrice.png',
                className='card-image',
                style={'width': '100%', 'height': '200px', 'objectFit': 'cover', 'borderRadius': '8px 8px 0 0'}
            ),
            html.Div([
                html.Div(restaurant['Name'], style={
                    'color': '#ffffff',
                    'fontSize': '1.2rem',
                    'fontWeight': 'bold',
                    'marginBottom': '0.5rem'
                }),
                html.Div(f"{restaurant.get('FirstCategory', 'Restaurant')} - {restaurant.get('SecondCategory', '')}",
                        style={'color': '#deb522', 'fontSize': '0.9rem', 'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span([
                        html.I(className='fas fa-star', style={'color': '#deb522', 'marginRight': '5px'}),
                        f"{restaurant['TotalRating']:.1f}"
                    ], style={'marginRight': '1rem'}),
                    html.Span([
                        html.I(className='fas fa-comment', style={'color': '#888', 'marginRight': '5px'}),
                        f"{int(restaurant.get('ReviewNum', 0))} reviews"
                    ])
                ], style={'color': '#aaaaaa', 'fontSize': '0.85rem', 'marginBottom': '0.5rem'}),
                html.Div([
                    html.I(className='fas fa-map-marker-alt', style={'marginRight': '5px'}),
                    restaurant.get('Station', 'Kyoto')
                ], style={'color': '#888888', 'fontSize': '0.85rem'})
            ], style={'padding': '1rem'})
        ], style={
            'backgroundColor': '#1a1a1a',
            'borderRadius': '8px',
            'overflow': 'hidden',
            'border': '1px solid #333',
            'transition': 'transform 0.2s, border-color 0.2s',
            'cursor': 'pointer'
        }, className='restaurant-list-card')

        # 包裝在可點擊的容器中，使用 pattern-matching ID
        card_wrapper = html.Div(
            card_content,
            id={'type': 'restaurant-card', 'index': restaurant['Restaurant_ID']},
            n_clicks=0
        )
        cards.append(card_wrapper)

    # Create grid layout
    grid = html.Div(cards, style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fill, minmax(300px, 1fr))',
        'gap': '1.5rem',
        'maxWidth': '1400px',
        'margin': '0 auto'
    })

    # Create pagination controls
    pagination = create_pagination_buttons(current_page, total_pages)

    # Search stats
    stats_text = f"Showing {start_idx + 1}-{end_idx} of {total_items} restaurants"

    return grid, pagination, stats_text

# Handle pagination button clicks
@app.callback(
    Output('current-page-store', 'data', allow_duplicate=True),
    [Input({'type': 'page-btn', 'index': ALL}, 'n_clicks')],
    [State('current-page-store', 'data'),
     State('search-results-store', 'data')],
    prevent_initial_call=True
)
def handle_pagination_click(n_clicks_list, current_page, search_results):
    """處理分頁按鈕點擊"""
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    # Get which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # safer: parse JSON id rather than eval
    import json as _json
    button_data = _json.loads(button_id)
    page_index = button_data['index']

    # Calculate total pages
    items_per_page = 15
    total_items = len(search_results) if search_results else 0
    total_pages = (total_items + items_per_page - 1) // items_per_page

    # Handle different button types
    if page_index == 'prev':
        new_page = max(1, current_page - 1)
    elif page_index == 'next':
        new_page = min(total_pages, current_page + 1)
    else:
        new_page = page_index

    return new_page

# Toggle user dropdown in restaurant list page
@app.callback(
    [Output('user-dropdown-list', 'className'),
     Output('dropdown-open-list', 'data')],
    [Input('user-avatar-list', 'n_clicks')],
    [State('dropdown-open-list', 'data')],
    prevent_initial_call=True
)
def toggle_user_dropdown_list(n_clicks, is_open):
    """切換餐廳列表頁的使用者下拉選單"""
    if n_clicks:
        new_state = not is_open
        className = 'user-dropdown show' if new_state else 'user-dropdown'
        return className, new_state
    raise PreventUpdate

# Handle logout from restaurant list page dropdown
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout-list', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_dropdown_list(n_clicks, session_data):
    """從餐廳列表頁下拉選單登出"""
    if not n_clicks:
        raise PreventUpdate

    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])

    return None

# Toggle user dropdown in hotel list page
@app.callback(
    [Output('user-dropdown-hotel-list', 'className'),
     Output('dropdown-open-hotel-list', 'data')],
    [Input('user-avatar-hotel-list', 'n_clicks')],
    [State('dropdown-open-hotel-list', 'data')],
    prevent_initial_call=True
)
def toggle_user_dropdown_hotel_list(n_clicks, is_open):
    """切換旅館列表頁的使用者下拉選單"""
    if n_clicks:
        new_state = not is_open
        className = 'user-dropdown show' if new_state else 'user-dropdown'
        return className, new_state
    raise PreventUpdate

# Handle logout from hotel list page dropdown
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout-hotel-list', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_dropdown_hotel_list(n_clicks, session_data):
    """從旅館列表頁下拉選單登出"""
    if not n_clicks:
        raise PreventUpdate

    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])

    return None

# ====== Profile Page Callbacks ======

# Navigate to profile page from home dropdown
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('dropdown-profile', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_to_profile_from_home(n_clicks):
    """從首頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        return 'profile'
    raise PreventUpdate

# Navigate to profile page from restaurant list dropdown
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('dropdown-profile-list', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_to_profile_from_restaurant_list(n_clicks):
    """從餐廳列表頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        return 'profile'
    raise PreventUpdate

# Navigate to profile page from hotel list dropdown
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('dropdown-profile-hotel-list', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_to_profile_from_hotel_list(n_clicks):
    """從旅館列表頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        return 'profile'
    raise PreventUpdate

# Back button from profile page
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('back-from-profile', 'n_clicks')],
    prevent_initial_call=True
)
def back_from_profile(n_clicks):
    """從個人檔案頁返回首頁"""
    if n_clicks:
        return 'home'
    raise PreventUpdate

# Toggle user dropdown in profile page
@app.callback(
    [Output('user-dropdown-profile', 'className'),
     Output('dropdown-open', 'data', allow_duplicate=True)],
    [Input('user-avatar-profile', 'n_clicks')],
    [State('dropdown-open', 'data')],
    prevent_initial_call=True
)
def toggle_user_dropdown_profile(n_clicks, is_open):
    """切換個人檔案頁使用者下拉選單"""
    if n_clicks:
        new_state = not is_open
        className = 'user-dropdown show' if new_state else 'user-dropdown'
        return className, new_state
    raise PreventUpdate

# Logout from profile page
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout-profile', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_profile(n_clicks, session_data):
    """從個人檔案頁登出"""
    if not n_clicks:
        raise PreventUpdate

    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])

    return None

# Navigate to profile page from restaurant detail page dropdown
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('menu-profile-detail', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_to_profile_from_restaurant_detail(n_clicks):
    """從餐廳詳細頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        return 'profile'
    raise PreventUpdate

# Navigate to profile page from hotel detail page dropdown
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('menu-profile-hotel-detail', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_to_profile_from_hotel_detail(n_clicks):
    """從旅館詳細頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        return 'profile'
    raise PreventUpdate

# ====== Hotel List Page Callbacks ======

# Display hotel list page
@app.callback(
    Output('page-content', 'children', allow_duplicate=True),
    [Input('view-mode', 'data')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def display_hotel_list_page(view_mode, session_data):
    """顯示旅館列表頁面"""
    if not (session_data and 'session_id' in session_data):
        raise PreventUpdate
    
    if view_mode == 'hotel-list':
        return create_hotel_list_page()
    
    raise PreventUpdate

# Handle hotel list search
@app.callback(
    [Output('hotel-search-results-store', 'data'),
     Output('hotel-current-page-store', 'data')],
    [Input('search-hotel-btn', 'n_clicks'),
     Input('search-hotel-type', 'data')],
    [State('search-hotel', 'value'),
     State('view-mode', 'data')],
    prevent_initial_call=True
)
def handle_hotel_list_search(n_clicks, hotel_type, keyword, view_mode):
    """處理旅館列表頁搜尋"""
    if view_mode != 'hotel-list':
        raise PreventUpdate
    
    filtered_hotels = search_hotels(
        keyword=keyword,
        hotel_type=hotel_type,
        sort_by='rating_desc'
    )
    
    search_results = filtered_hotels.to_dict('records') if len(filtered_hotels) > 0 else []
    return search_results, 1

# Update hotel grid
@app.callback(
    [Output('hotel-grid', 'children'),
     Output('hotel-pagination-controls', 'children'),
     Output('hotel-search-stats', 'children')],
    [Input('hotel-search-results-store', 'data'),
     Input('hotel-current-page-store', 'data')],
    prevent_initial_call=False
)
def update_hotel_grid(search_results, current_page):
    """更新旅館網格和分頁"""
    if search_results is None:
        df = search_hotels(sort_by='rating_desc')
        search_results = df.to_dict('records')
    
    if not search_results:
        return (
            html.Div([
                html.I(className='fas fa-hotel', style={'fontSize': '4rem', 'color': '#deb522', 'marginBottom': '2rem'}),
                html.H3('No hotels found', style={'color': '#ffffff'}),
                html.P('Try adjusting your search criteria', style={'color': '#888888'})
            ], style={'textAlign': 'center', 'padding': '4rem'}),
            html.Div(),
            ''
        )
    
    # 分頁邏輯
    items_per_page = 15
    total_items = len(search_results)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_items = search_results[start_idx:end_idx]
    
    # 創建旅館卡片
    cards = []
    for hotel in current_items:
        types_text = ', '.join(hotel['Types'][:2]) if isinstance(hotel['Types'], list) and hotel['Types'] else 'Hotel'
        
        card_content = html.Div([
            html.Img(
                src='/assets/food_dirtyrice.png',
                style={'width': '100%', 'height': '200px', 'objectFit': 'cover', 'borderRadius': '8px 8px 0 0'}
            ),
            html.Div([
                html.Div(hotel['HotelName'], style={'color': '#ffffff', 'fontSize': '1.2rem', 'fontWeight': 'bold', 'marginBottom': '0.5rem'}),
                html.Div(types_text, style={'color': '#deb522', 'fontSize': '0.9rem', 'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span([
                        html.I(className='fas fa-star', style={'color': '#deb522', 'marginRight': '5px'}),
                        f"{hotel['Rating']:.1f}"
                    ], style={'marginRight': '1rem'}),
                    html.Span([
                        html.I(className='fas fa-comment', style={'color': '#888', 'marginRight': '5px'}),
                        f"{int(hotel.get('UserRatingsTotal', 0))} reviews"
                    ])
                ], style={'color': '#aaaaaa', 'fontSize': '0.85rem', 'marginBottom': '0.5rem'}),
                html.Div([
                    html.I(className='fas fa-map-marker-alt', style={'marginRight': '5px'}),
                    hotel['Address'][:40] + '...' if len(hotel['Address']) > 40 else hotel['Address']
                ], style={'color': '#888888', 'fontSize': '0.85rem'})
            ], style={'padding': '1rem'})
        ], style={
            'backgroundColor': '#1a1a1a',
            'borderRadius': '8px',
            'overflow': 'hidden',
            'border': '1px solid #333',
            'transition': 'transform 0.2s, border-color 0.2s',
            'cursor': 'pointer'
        })
        
        card_wrapper = html.Div(
            card_content,
            id={'type': 'hotel-card', 'index': hotel['Hotel_ID']},
            n_clicks=0
        )
        cards.append(card_wrapper)
    
    # 創建網格
    grid = html.Div(cards, style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fill, minmax(300px, 1fr))',
        'gap': '1.5rem',
        'maxWidth': '1400px',
        'margin': '0 auto'
    })
    
    # 創建分頁按鈕 (複用餐廳的函數)
    pagination = create_pagination_buttons(current_page, total_pages)
    
    stats_text = f"Showing {start_idx + 1}-{end_idx} of {total_items} hotels"
    
    return grid, pagination, stats_text



##########################################################
####  餐廳詳細頁面 Callbacks (Restaurant Detail Page)  ####
##########################################################

# Callback 1: Route Detector - 解析 URL 中的餐廳 ID
@app.callback(
    [Output('selected-restaurant-id', 'data'),
     Output('previous-page-location', 'data')],
    [Input('url', 'pathname')],
    prevent_initial_call=False
)
def detect_restaurant_route(pathname):
    """解析 URL pathname 來提取餐廳 ID 並追蹤導航來源"""
    if pathname and pathname.startswith('/restaurant/'):
        try:
            # 從 URL 中提取餐廳 ID
            restaurant_id = int(pathname.split('/')[-1])
            return {'id': restaurant_id}, {'from': 'restaurant-list'}
        except (ValueError, IndexError):
            # 無效的餐廳 ID
            return {'id': None}, {'from': 'home'}
    elif pathname == '/restaurant-list':
        return {'id': None}, {'from': 'home'}
    else:
        return {'id': None}, {'from': 'home'}

# Callback 2: Data Loader - 從數據庫載入餐廳數據
@app.callback(
    Output('restaurant-detail-data', 'data'),
    [Input('selected-restaurant-id', 'data')],
    prevent_initial_call=True
)
def load_restaurant_detail(restaurant_id_data):
    """從數據庫獲取餐廳詳細資料並附帶 ALL 評論（若存在）"""
    if not restaurant_id_data or not restaurant_id_data.get('id'):
        raise PreventUpdate

    restaurant_id = restaurant_id_data['id']

    try:
        restaurant_data = get_restaurant_by_id(restaurant_id)
        if not restaurant_data:
            return {'error': 'Restaurant not found', 'id': restaurant_id}

        # 將 restaurant_data 轉為 dict（可序列化）
        try:
            if not isinstance(restaurant_data, dict):
                restaurant_data = dict(restaurant_data)
        except Exception:
            restaurant_data = {'error': 'Invalid restaurant data format', 'id': restaurant_id}

        # Load reviews from CSV if available and attach ALL comments for this restaurant
        reviews_list = []
        try:
            reviews_df = pd.read_csv('data/Reviews.csv', encoding='utf-8-sig')
            # detect restaurant id column
            id_cols = [c for c in reviews_df.columns if c.lower().replace('-', '_') in ('restaurant_id', 'restaurantid')]
            if id_cols:
                id_col = id_cols[0]
                filt = reviews_df[reviews_df[id_col] == restaurant_id]
            else:
                filt = pd.DataFrame()

            for _, row in filt.iterrows():
                # detect rating and comment columns with common names
                rating = None
                for rc in ('Review_Rating', 'ReviewRating', 'Rating', 'rating', 'review_rating'):
                    if rc in row.index:
                        rating = row[rc]
                        break
                comment = None
                for cc in ('Review_Text', 'ReviewText', 'Comment', 'comment', 'Review'):
                    if cc in row.index:
                        comment = row[cc]
                        break
                reviews_list.append({'rating': rating, 'comment': comment})
        except FileNotFoundError:
            reviews_list = []
        except Exception:
            reviews_list = []

        restaurant_data['reviews'] = reviews_list
        return restaurant_data

    except Exception as e:
        return {'error': str(e), 'id': restaurant_id}

# Callback 3: Content Renderer - 渲染詳細頁面內容
@app.callback(
    Output('restaurant-detail-content', 'children'),
    [Input('restaurant-detail-data', 'data')],
    prevent_initial_call=True
)
def render_restaurant_detail(restaurant_data):
    """根據餐廳數據渲染詳細頁面內容"""
    if not restaurant_data:
        return create_loading_state()

    if 'error' in restaurant_data:
        return create_error_state(restaurant_data.get('error', 'An error occurred'))

    # 渲染完整的詳細頁面
    return create_restaurant_detail_content(restaurant_data)


# ====== Hotel detail data loader (attach reviews) ======
@app.callback(
    Output('hotel-detail-data', 'data'),
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def load_hotel_detail_data(pathname):
    """從資料庫獲取旅館詳細資料並附帶所有評論（若存在）"""
    if not (pathname and pathname.startswith('/hotel/')):
        raise PreventUpdate

    try:
        hotel_id = int(pathname.split('/')[-1])
    except Exception:
        return {'error': 'Invalid hotel id', 'id': None}

    print(f"🔍 DEBUG: load_hotel_detail_data triggered for pathname={pathname}, hotel_id={hotel_id}")

    try:
        hotel_data = get_hotel_by_id(hotel_id)
        if not hotel_data:
            return {'error': 'Hotel not found', 'id': hotel_id}

        # ensure dict
        try:
            if not isinstance(hotel_data, dict):
                hotel_data = dict(hotel_data)
        except Exception:
            hotel_data = {'error': 'Invalid hotel data format', 'id': hotel_id}

        # Load hotel reviews CSV if present
        reviews_list = []
        try:
            reviews_df = pd.read_csv('data/HotelReviews.csv', encoding='utf-8-sig')
            # detect hotel id column name
            id_cols = [c for c in reviews_df.columns if c.lower().replace('-', '_') in ('hotel_id', 'hotelid')]
            if id_cols:
                id_col = id_cols[0]
                filt = reviews_df[reviews_df[id_col] == hotel_id]
            else:
                filt = pd.DataFrame()

            for _, row in filt.iterrows():
                rating = None
                for rc in ('Review_Rating', 'ReviewRating', 'Rating', 'rating', 'review_rating'):
                    if rc in row.index:
                        rating = row[rc]
                        break
                comment = None
                for cc in ('Review_Text', 'ReviewText', 'Comment', 'comment', 'Review'):
                    if cc in row.index:
                        comment = row[cc]
                        break
                reviews_list.append({'rating': rating, 'comment': comment})
        except FileNotFoundError:
            reviews_list = []
        except Exception:
            reviews_list = []

        hotel_data['reviews'] = reviews_list
        return hotel_data
    except Exception as e:
        return {'error': str(e), 'id': hotel_id}

# Callback 4: Card Click Handler - 處理餐廳卡片點擊事件
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input({'type': 'restaurant-card', 'index': ALL}, 'n_clicks')],
    [State({'type': 'restaurant-card', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def handle_card_click(n_clicks_list, card_ids):
    """處理餐廳卡片點擊，導航到詳細頁面"""
    ctx = callback_context

    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    # 確定哪個卡片被點擊
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_dict = json.loads(triggered_id)
    restaurant_id = triggered_dict['index']

    # 導航到詳細頁面
    return f'/restaurant/{restaurant_id}'

# Callback 4b: Nearby Restaurant Card Click Handler - 處理附近餐廳卡片點擊事件
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input({'type': 'nearby-restaurant-card', 'index': ALL}, 'n_clicks')],
    [State({'type': 'nearby-restaurant-card', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def handle_nearby_card_click(n_clicks_list, card_ids):
    """處理附近餐廳卡片點擊，導航到該餐廳詳細頁面"""
    ctx = callback_context

    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    # 確定哪個卡片被點擊
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_dict = json.loads(triggered_id)
    restaurant_id = triggered_dict['index']

    # 導航到詳細頁面
    return f'/restaurant/{restaurant_id}'

# Callback 5: Back Button Handler - 處理返回按鈕
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('view-mode', 'data', allow_duplicate=True)],
    [Input('restaurant-detail-back-btn', 'n_clicks')],
    [State('previous-page-location', 'data')],
    prevent_initial_call=True
)
def handle_back_button(n_clicks, previous_page):
    """處理返回按鈕點擊，導航回上一頁"""
    if not n_clicks:
        raise PreventUpdate

    if previous_page and previous_page.get('from') == 'restaurant-list':
        return '/restaurant-list', 'restaurant-list'
    else:
        return '/', 'home'

# Callback 6: Error Back Button Handler - 處理錯誤頁面的返回按鈕
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('view-mode', 'data', allow_duplicate=True)],
    [Input('error-back-btn', 'n_clicks')],
    prevent_initial_call=True
)
def handle_error_back_button(n_clicks):
    """處理錯誤頁面返回按鈕"""
    if not n_clicks:
        raise PreventUpdate

    return '/', 'home'

# Callback 7: User Dropdown Toggle (Restaurant Detail Page) - 餐廳詳細頁面用戶下拉菜單
@app.callback(
    [Output('user-dropdown-detail', 'className'),
     Output('dropdown-open-detail', 'data')],
    [Input('user-avatar-detail', 'n_clicks')],
    [State('dropdown-open-detail', 'data')],
    prevent_initial_call=True
)
def toggle_user_dropdown_detail(n_clicks, is_open):
    """切換餐廳詳細頁面的用戶下拉菜單"""
    if n_clicks:
        new_state = not is_open
        className = 'user-dropdown show' if new_state else 'user-dropdown'
        return className, new_state
    raise PreventUpdate

# Callback 7b: User Dropdown Toggle (Hotel Detail Page) - 旅館詳細頁面用戶下拉菜單
@app.callback(
    [Output('user-dropdown-detail', 'className', allow_duplicate=True),
     Output('dropdown-open-detail', 'data', allow_duplicate=True)],
    [Input('user-avatar-hotel-detail', 'n_clicks')],
    [State('dropdown-open-detail', 'data')],
    prevent_initial_call=True
)
def toggle_user_dropdown_hotel_detail(n_clicks, is_open):
    """切換旅館詳細頁面的用戶下拉菜單"""
    if n_clicks:
        new_state = not is_open
        className = 'user-dropdown show' if new_state else 'user-dropdown'
        return className, new_state
    raise PreventUpdate

# Callback 7c: Reset All Dropdown States on Outside Click - 點擊外部時重置所有下拉菜單狀態
@app.callback(
    [Output('dropdown-open', 'data', allow_duplicate=True),
     Output('dropdown-open-list', 'data', allow_duplicate=True),
     Output('dropdown-open-hotel-list', 'data', allow_duplicate=True),
     Output('dropdown-open-detail', 'data', allow_duplicate=True)],
    [Input('close-dropdowns-trigger', 'data')],
    prevent_initial_call=True
)
def reset_all_dropdown_states(trigger):
    """當用戶點擊外部時，重置所有下拉菜單的狀態"""
    if trigger is not None:
        return False, False, False, False
    raise PreventUpdate

# Callback 8: Logout from Detail Page - 從詳細頁面登出
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout-detail', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_detail_page(n_clicks, session_data):
    """從詳細頁面下拉選單登出"""
    if not n_clicks:
        raise PreventUpdate

    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])

    return None

# 點擊星等長條圖顯示該星級部分評論，並提供 Show all 按鈕
@app.callback(
    Output('reviews-comments', 'children'),
    [Input('ratings-bar-chart', 'clickData'),
     Input({'type': 'show-all-comments', 'index': ALL}, 'n_clicks')],
    [State('restaurant-detail-data', 'data'),
     State('hotel-detail-data', 'data')],
    prevent_initial_call=True
)
def handle_reviews_interaction(clickData, show_all_n_clicks, restaurant_data, hotel_data):
    """Handle both rating-bar clicks (show sample + Show all button) and Show all button clicks.

    Supports both restaurant and hotel detail stores (prefers restaurant data if present).
    """
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Choose which detail data to use (restaurant preferred)
    detail_data = None
    if isinstance(restaurant_data, dict) and restaurant_data:
        detail_data = restaurant_data
    elif isinstance(hotel_data, dict) and hotel_data:
        detail_data = hotel_data
    else:
        detail_data = {}

    # Safely get reviews list
    reviews = detail_data.get('reviews', []) if isinstance(detail_data, dict) else []

    # If the ratings bar was clicked
    if triggered_id == 'ratings-bar-chart':
        if not clickData:
            raise PreventUpdate
        try:
            clicked_star = int(clickData['points'][0]['x'])
        except Exception:
            return html.Div('Unable to parse clicked rating', style={'color': '#888888'})

        matched = [r for r in reviews if r and r.get('rating') is not None and int(round(float(r['rating']))) == clicked_star]

        if not matched:
            return html.Div(f'No comments for {clicked_star}★', style={'color': '#888888'})

        items = []
        for r in matched[:6]:
            text = r.get('comment') or 'No comment text'
            items.append(html.Div([
                html.Div(f"★ {clicked_star}", style={'color': '#deb522', 'fontWeight': '600', 'marginRight': '8px', 'display': 'inline-block', 'width': '48px'}),
                html.Div(text, style={'color': '#ffffff', 'display': 'inline-block', 'verticalAlign': 'top', 'maxWidth': 'calc(100% - 60px)'})
            ], style={'padding': '8px 0', 'borderBottom': '1px solid #222'}))

        # Add Show all button if more comments exist
        if len(matched) > 6:
            items.append(html.Div([
                html.Button('Show all comments', id={'type': 'show-all-comments', 'index': clicked_star}, n_clicks=0, className='btn-primary', style={'marginTop': '10px'})
            ], style={'textAlign': 'center'}))

        return html.Div(items)

    # Otherwise a "Show all" button was clicked (pattern-matching id)
    else:
        try:
            triggered_obj = json.loads(triggered_id)
        except Exception:
            raise PreventUpdate

        if triggered_obj.get('type') != 'show-all-comments':
            raise PreventUpdate

        star = int(triggered_obj['index'])

        matched = [r for r in reviews if r and r.get('rating') is not None and int(round(float(r['rating']))) == star]

        if not matched:
            return html.Div(f'No comments for {star}★', style={'color': '#888888'})

        items = []
        for r in matched:
            text = r.get('comment') or 'No comment text'
            items.append(html.Div([
                html.Div(f"★ {star}", style={'color': '#deb522', 'fontWeight': '600', 'marginRight': '8px', 'display': 'inline-block', 'width': '48px'}),
                html.Div(text, style={'color': '#ffffff', 'display': 'inline-block', 'verticalAlign': 'top', 'maxWidth': 'calc(100% - 60px)'})
            ], style={'padding': '8px 0', 'borderBottom': '1px solid #222'}))

        return html.Div(items)
    
##########################################################
####  旅館詳細頁面 Callbacks (Hotel Detail Page)  ####
##########################################################

# Callback 1: Handle hotel card click
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input({'type': 'hotel-card', 'index': ALL}, 'n_clicks')],
    [State({'type': 'hotel-card', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def handle_hotel_card_click(n_clicks_list, card_ids):
    """處理旅館卡片點擊，導航到詳細頁面"""
    ctx = callback_context
    
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_dict = json.loads(triggered_id)
    hotel_id = triggered_dict['index']
    
    print(f"🔍 DEBUG: Hotel card clicked! hotel_id={hotel_id}")  # Debug 訊息
    
    return f'/hotel/{hotel_id}'

# Callback 3: Render hotel detail content when hotel-detail-data store is populated
@app.callback(
    Output('hotel-detail-content', 'children'),
    [Input('hotel-detail-data', 'data')],
    prevent_initial_call=True
)
def render_hotel_detail(hotel_data):
    """根據 hotel-detail-data store 渲染旅館詳細內容（與餐廳流程一致）"""
    print("🔍 DEBUG: render_hotel_detail called")
    if not hotel_data:
        print("🔍 DEBUG: hotel_data empty")
        return create_loading_state()

    if isinstance(hotel_data, dict) and 'error' in hotel_data:
        return create_error_state(hotel_data.get('error', 'An error occurred'))

    return create_hotel_detail_content(hotel_data)

# Callback 4: Load nearby hotels
@app.callback(
    Output('nearby-hotels-section', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def load_nearby_hotels(pathname):
    """載入附近旅館列表"""
    if pathname and pathname.startswith('/hotel/'):
        try:
            hotel_id = int(pathname.split('/')[-1])
            hotel_data = get_hotel_by_id(hotel_id)
            
            if not hotel_data:
                raise PreventUpdate
            
            lat = hotel_data.get('Lat')
            lon = hotel_data.get('Long')
            
            if lat is None or lon is None:
                return html.Div()
            
            nearby_hotels = get_nearby_hotels(lat, lon, limit=5, exclude_id=hotel_id)
            
            if not nearby_hotels:
                return html.Div()
            
            nearby_cards = []
            for i, nearby in enumerate(nearby_hotels, 1):
                card = html.Div([
                    html.Div([
                        html.Div(f"{i}", style={
                            'backgroundColor': '#deb522',
                            'color': '#000',
                            'width': '24px',
                            'height': '24px',
                            'borderRadius': '50%',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'fontSize': '0.85rem',
                            'fontWeight': 'bold',
                            'marginRight': '12px'
                        }),
                        html.Div([
                            html.Div(nearby['HotelName'], style={'color': '#ffffff', 'fontWeight': '600'}),
                            html.Div([
                                html.Span([
                                    html.I(className='fas fa-star', style={'color': '#deb522', 'marginRight': '4px'}),
                                    f"{nearby['Rating']:.1f}"
                                ], style={'marginRight': '12px'}),
                                html.Span(f"{nearby['distance']:.2f} km", style={'color': '#888'})
                            ], style={'fontSize': '0.85rem', 'marginTop': '4px'})
                        ])
                    ], style={'display': 'flex', 'alignItems': 'center', 'padding': '12px',
                             'backgroundColor': '#1a1a1a', 'border': '1px solid #333',
                             'borderRadius': '8px', 'marginBottom': '8px', 'cursor': 'pointer'})
                ], id={'type': 'nearby-hotel-card', 'index': nearby['Hotel_ID']}, n_clicks=0)
                nearby_cards.append(card)
            
            return html.Div([
                html.H4([
                    html.I(className='fas fa-hotel', style={'marginRight': '8px', 'color': '#deb522'}),
                    f'Nearby Hotels ({len(nearby_hotels)})'
                ], style={'color': '#ffffff', 'fontSize': '1.1rem', 'marginBottom': '1rem'}),
                html.Div(nearby_cards)
            ], style={
                'backgroundColor': '#1a1a1a',
                'border': '1px solid #333',
                'borderRadius': '12px',
                'padding': '1.5rem'
            })
        except:
            return html.Div()
    
    raise PreventUpdate

# Callback 5: Handle nearby hotel click
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input({'type': 'nearby-hotel-card', 'index': ALL}, 'n_clicks')],
    [State({'type': 'nearby-hotel-card', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def handle_nearby_hotel_click(n_clicks_list, card_ids):
    """處理附近旅館卡片點擊"""
    ctx = callback_context
    
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_dict = json.loads(triggered_id)
    hotel_id = triggered_dict['index']
    
    return f'/hotel/{hotel_id}'

# Callback 6: Handle back button
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input('hotel-detail-back-btn', 'n_clicks')],
    prevent_initial_call=True
)
def handle_hotel_back_button(n_clicks):
    """處理旅館詳情頁返回按鈕"""
    if n_clicks:
        return '/'
    raise PreventUpdate
##########################################################

# ====== Image Gallery Carousel Callbacks ======

# Callback 1: Update current image index and toggle layer based on navigation and autoplay
@app.callback(
    [Output('gallery-current-index', 'data'),
     Output('gallery-layer-toggle', 'data')],
    [Input('gallery-prev-btn', 'n_clicks'),
     Input('gallery-next-btn', 'n_clicks'),
     Input({'type': 'gallery-indicator', 'index': ALL}, 'n_clicks'),
     Input('gallery-autoplay-interval', 'n_intervals')],
    [State('gallery-current-index', 'data'),
     State('gallery-images-list', 'data'),
     State('gallery-layer-toggle', 'data')],
    prevent_initial_call=True
)
def update_gallery_index(prev_clicks, next_clicks, indicator_clicks, n_intervals, current_index, images_list, layer_toggle):
    """更新圖片畫廊當前索引（自動播放+手動導航）並切換圖層"""
    if not images_list:
        raise PreventUpdate

    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    num_images = len(images_list)

    # 處理自動播放（每4秒自動切換）
    if triggered_id == 'gallery-autoplay-interval':
        return (current_index + 1) % num_images, not layer_toggle

    # 處理上一張按鈕
    elif triggered_id == 'gallery-prev-btn':
        return (current_index - 1) % num_images, not layer_toggle

    # 處理下一張按鈕
    elif triggered_id == 'gallery-next-btn':
        return (current_index + 1) % num_images, not layer_toggle

    # 處理指示器點擊
    else:
        try:
            triggered_dict = json.loads(triggered_id)
            if triggered_dict.get('type') == 'gallery-indicator':
                return triggered_dict['index'], not layer_toggle
        except:
            pass

    raise PreventUpdate

# Callback 2: Update displayed images with crossfade effect
@app.callback(
    [Output('gallery-image-bg', 'style'),
     Output('gallery-image-fg', 'style')],
    [Input('gallery-current-index', 'data'),
     Input('gallery-layer-toggle', 'data')],
    [State('gallery-images-list', 'data')],
    prevent_initial_call=True
)
def update_gallery_images_crossfade(current_index, layer_toggle, images_list):
    """更新圖片（交叉淡入淡出效果）- 使用圖層切換實現流暢過渡"""
    if not images_list or current_index is None:
        raise PreventUpdate

    # 確保索引在範圍內
    if not (0 <= current_index < len(images_list)):
        raise PreventUpdate

    current_image = images_list[current_index]

    # 基礎樣式
    base_style = {
        'width': '100%',
        'height': '100%',
        'backgroundSize': 'cover',
        'backgroundPosition': 'center',
        'position': 'absolute',
        'top': '0',
        'left': '0',
        'transition': 'opacity 1.5s cubic-bezier(0.4, 0, 0.2, 1)',  # 使用更流暢的緩動函數
    }

    # 根據toggle狀態決定哪一層顯示在前面
    if layer_toggle:
        # 前景層顯示當前圖片（淡入）
        bg_style = {
            **base_style,
            'backgroundImage': f'url({images_list[(current_index - 1) % len(images_list)]})',
            'opacity': '0',
            'pointerEvents': 'none'
        }
        fg_style = {
            **base_style,
            'backgroundImage': f'url({current_image})',
            'opacity': '1',
            'pointerEvents': 'none'
        }
    else:
        # 背景層顯示當前圖片（淡入）
        bg_style = {
            **base_style,
            'backgroundImage': f'url({current_image})',
            'opacity': '1'
        }
        fg_style = {
            **base_style,
            'backgroundImage': f'url({images_list[(current_index - 1) % len(images_list)]})',
            'opacity': '0',
            'pointerEvents': 'none'
        }

    return bg_style, fg_style

# Callback 3: Update active indicator
@app.callback(
    [Output({'type': 'gallery-indicator', 'index': ALL}, 'className')],
    [Input('gallery-current-index', 'data')],
    [State('gallery-images-list', 'data')],
    prevent_initial_call=True
)
def update_gallery_indicators(current_index, images_list):
    """更新指示器的 active 狀態"""
    if not images_list or current_index is None:
        raise PreventUpdate

    num_images = len(images_list)

    # 為每個指示器生成className
    classnames = []
    for i in range(num_images):
        if i == current_index:
            classnames.append('gallery-indicator active')
        else:
            classnames.append('gallery-indicator')

    return [classnames]

# Register analytics callbacks
register_analytics_callbacks(app, analytics_df)

@app.callback(
    Output('map-container', 'children'),
    Input('map-type-switch', 'value')
)
def update_map(selected_map):
    if selected_map == 'restaurants':
        return create_restaurant_map_chart()
    elif selected_map == 'hotels':
        return create_hotel_map_chart()
    return html.Div()

# ===== Callback: Restaurant Map Click Navigation =====
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('restaurant-map-graph', 'clickData'),
    prevent_initial_call=True
)
def navigate_from_restaurant_map(click_data):
    if click_data is None:
        raise PreventUpdate

    try:
        # Extract Restaurant ID from customdata
        restaurant_id = click_data['points'][0]['customdata'][0]
        print(f"Restaurant map clicked - ID: {restaurant_id}")  # Debug log

        # Navigate to restaurant detail page
        return f'/restaurant/{int(restaurant_id)}'
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error handling restaurant map click: {e}")
        print(f"Click data: {click_data}")
        raise PreventUpdate

# ===== Callback: Hotel Map Click Navigation =====
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('hotel-map-graph', 'clickData'),
    prevent_initial_call=True
)
def navigate_from_hotel_map(click_data):
    if click_data is None:
        raise PreventUpdate

    try:
        # Extract Hotel ID from customdata
        hotel_id = click_data['points'][0]['customdata'][0]
        print(f"Hotel map clicked - ID: {hotel_id}")  # Debug log

        # Navigate to hotel detail page
        return f'/hotel/{int(hotel_id)}'
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error handling hotel map click: {e}")
        print(f"Click data: {click_data}")
        raise PreventUpdate

# ===== Clientside Callback: Scroll to Top on Page Change =====
app.clientside_callback(
    """
    function(currentPage) {
        if (currentPage !== undefined && currentPage !== null && currentPage > 0) {
            setTimeout(function() {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }, 50);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('scroll-trigger', 'children'),
    Input('current-page-store', 'data')
)

# ===== Clientside Callback: Close Dropdowns on Outside Click =====
app.clientside_callback(
    """
    function(pathname) {
        // Add click event listener to document
        if (!window.dropdownClickListenerAdded) {
            document.addEventListener('click', function(event) {
                // Get all dropdown containers
                const dropdownIds = [
                    'user-dropdown',
                    'user-dropdown-list',
                    'user-dropdown-hotel-list',
                    'user-dropdown-detail'
                ];

                const avatarIds = [
                    'user-avatar',
                    'user-avatar-list',
                    'user-avatar-hotel-list',
                    'user-avatar-detail',
                    'user-avatar-hotel-detail'
                ];

                // Check if click is on avatar (toggle should handle it)
                let clickedAvatar = false;
                for (let avatarId of avatarIds) {
                    const avatar = document.getElementById(avatarId);
                    if (avatar && avatar.contains(event.target)) {
                        clickedAvatar = true;
                        break;
                    }
                }

                // If clicked on avatar, don't close (let toggle handle it)
                if (clickedAvatar) {
                    return;
                }

                // Check if click is outside all dropdowns
                let clickedOutside = true;
                for (let dropdownId of dropdownIds) {
                    const dropdown = document.getElementById(dropdownId);
                    if (dropdown && dropdown.contains(event.target)) {
                        clickedOutside = false;
                        break;
                    }
                }

                // If clicked outside, close all dropdowns
                if (clickedOutside) {
                    let anyClosed = false;
                    for (let dropdownId of dropdownIds) {
                        const dropdown = document.getElementById(dropdownId);
                        if (dropdown && dropdown.classList.contains('show')) {
                            dropdown.classList.remove('show');
                            anyClosed = true;
                        }
                    }

                    // Trigger server-side state updates if any dropdown was closed
                    if (anyClosed && window.dash_clientside) {
                        // Set the trigger value to current timestamp
                        window.dash_clientside.set_props('close-dropdowns-trigger', {data: Date.now()});
                    }
                }
            });
            window.dropdownClickListenerAdded = true;
        }

        return window.dash_clientside.no_update;
    }
    """,
    Output('url', 'pathname', allow_duplicate=True),
    Input('url', 'pathname'),
    prevent_initial_call=True
)

# --- 處理旅館詳細頁面的說明按鈕開關 ---
@app.callback(
    Output({'type': 'help-collapse-detail', 'index': MATCH}, 'is_open'),
    [Input({'type': 'help-btn-detail', 'index': MATCH}, 'n_clicks')],
    [State({'type': 'help-collapse-detail', 'index': MATCH}, 'is_open')]
)
def toggle_detail_help(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

if __name__ == '__main__':
    app.run(debug=True, port=8050)