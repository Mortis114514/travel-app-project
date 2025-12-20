# Import 所有相關套件
import os
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

import dash
from dash import Dash, html, dcc, Input, State, Output, dash_table, no_update, callback_context, ALL, MATCH
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import dash_leaflet as dl
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import uuid
import random
import json
import base64
import io
from datetime import datetime, timedelta
import functools
import plotly.graph_objects as go

# 從./utils導入所有自定義函數
from utils.auth import verify_user, create_user, get_session, create_session, delete_session, clean_expired_sessions, get_user_full_details, update_profile_photo
from pages.login_page import create_login_layout, create_register_layout
from pages.analytics_page import create_analytics_layout, load_and_prepare_data, register_analytics_callbacks
from utils.database import get_revenue_trend, get_occupancy_status

########################
#### 資料載入與前處理 ####
########################
# 導入數據庫工具 (已整理重複項)
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
    get_hotels_by_type,
    get_random_top_attractions, 
    search_attractions, 
    get_unique_attraction_types,
    get_attraction_by_id,
    get_all_attractions,
    get_combined_analytics_data,
    # 👇 關鍵的新函式
    initialize_database 
)

# ==========================
# 資料庫初始化與資料載入
# ==========================

# 1. 優先執行初始化：檢查資料表，若無則從 CSV 重建 (包含建立 Favorites/Trips 表)
# 這行會解決 "no such table: restaurants" 的錯誤
initialize_database()

# 2. 資料載入：將資料讀入 Pandas DataFrame (記憶體中)
try:
    print("Loading data into memory...")
    restaurants_df = get_all_restaurants()  # 從數據庫加載（用於選項列表）
    hotels_df = get_all_hotels()
    analytics_df = load_and_prepare_data()
    print("Data loaded successfully.")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    # 如果出錯，給予空的 DataFrame 防止 App 崩潰
    import pandas as pd
    restaurants_df = pd.DataFrame()
    hotels_df = pd.DataFrame()
    analytics_df = pd.DataFrame()


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

def create_attraction_type_options():
    """創建景點類型選項列表（包含清除選項）"""
    options = []
    # 清除選擇選項
    options.append(
        html.Div([
            html.I(className='fas fa-times', style={'marginRight': '8px'}),
            'Clear Selection'
        ],
        className='custom-dropdown-item',
        id={'type': 'attraction-type-option', 'index': '__CLEAR__'},
        n_clicks=0,
        style={'borderBottom': '2px solid rgba(222, 181, 34, 0.3)', 'fontWeight': '500'})
    )

    # 從數據庫獲取唯一的景點類型
    all_types = get_unique_attraction_types()

    # 其他選項
    for attr_type in all_types:
        options.append(
            html.Div(attr_type,
                    className='custom-dropdown-item',
                    id={'type': 'attraction-type-option', 'index': attr_type},
                    n_clicks=0)
        )
    return options

def create_attraction_rating_options():
    """創建景點評分選項列表（包含清除選項）"""
    options = []
    # 清除選擇選項
    options.append(
        html.Div([
            html.I(className='fas fa-times', style={'marginRight': '8px'}),
            'Clear Selection'
        ],
        className='custom-dropdown-item',
        id={'type': 'attraction-rating-option', 'index': '__CLEAR__'},
        n_clicks=0,
        style={'borderBottom': '2px solid rgba(222, 181, 34, 0.3)', 'fontWeight': '500'})
    )
    # 評分選項
    options.append(html.Div('⭐⭐⭐⭐⭐ 4~5 Stars',
                            className='custom-dropdown-item',
                            id={'type': 'attraction-rating-option', 'index': '4-5'},
                            n_clicks=0))
    options.append(html.Div('⭐⭐⭐⭐ 3~4 Stars',
                            className='custom-dropdown-item',
                            id={'type': 'attraction-rating-option', 'index': '3-4'},
                            n_clicks=0))
    options.append(html.Div('⭐⭐⭐ 2~3 Stars',
                            className='custom-dropdown-item',
                            id={'type': 'attraction-rating-option', 'index': '2-3'},
                            n_clicks=0))
    options.append(html.Div('⭐⭐ 1~2 Stars',
                            className='custom-dropdown-item',
                            id={'type': 'attraction-rating-option', 'index': '1-2'},
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

    # Use btn-create-trip class for Create a Trip button, otherwise use btn-primary
    btn_class = 'btn-primary btn-create-trip' if button_id == 'create-trip-btn' else 'btn-primary'

    return html.Button(
        children,
        id=button_id,
        className=btn_class,
        n_clicks=0
    )

def create_destination_card(restaurant, id_type='restaurant-card', is_favorite=False): # [新增] is_favorite 參數
    """創建目的地卡片 (支援自定義 ID 類型與收藏狀態)"""
    
    # 決定愛心圖示樣式 (實心/空心) 與顏色
    heart_icon = "fas fa-heart" if is_favorite else "far fa-heart"
    heart_color = "#ff4757" if is_favorite else "white"

    card_content = html.Div([
        # Image section (需加上 relative 定位以放置愛心)
        html.Div([
            html.Img(src='/assets/food_dirtyrice.png', className='card-image'),
            
            # [新增] 愛心按鈕
            html.Div(
                html.I(className=heart_icon, style={'color': heart_color, 'fontSize': '1.2rem'}),
                # ID 必須符合 Pattern Matching 格式：{'type': 'fav-btn', ...}
                id={'type': 'fav-btn', 'item_type': 'Restaurant', 'index': restaurant['Restaurant_ID']},
                n_clicks=0,
                # 樣式：絕對定位在右上角，半透明黑底
                style={
                    'position': 'absolute', 'top': '10px', 'right': '10px', 
                    'background': 'rgba(0,0,0,0.5)', 'borderRadius': '50%', 
                    'width': '35px', 'height': '35px', 'display': 'flex', 
                    'alignItems': 'center', 'justifyContent': 'center', 
                    'cursor': 'pointer', 'zIndex': '10'
                }
            )
        ], className='card-image-section', style={'position': 'relative'}), # 關鍵：父層要是 relative
        
        html.Div([
            html.Div(restaurant['Name'], className='card-title'),
            html.Div(restaurant.get('JapaneseName', ''), className='card-japanese-name'),
            html.Div(restaurant.get('FirstCategory', 'Restaurant'), className='card-subtitle'),
            html.Div([
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.Span(f"{restaurant['TotalRating']:.1f}")
            ], className='card-rating'),
        ], className='card-content-section')
    ])

    return html.Div(
        card_content,
        id={'type': id_type, 'index': restaurant['Restaurant_ID']},
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
                html.I(className='fas fa-search', style={'color': '#003580', 'fontSize': '1.2rem'}),
                dcc.Input(
                    id='search-destination',
                    type='text',
                    value='',
                    placeholder='Search restaurants by name (English or Japanese)...',
                    className='search-input',
                    debounce=False,  # 即時搜尋
                    style={
                        'background': 'transparent',
                        'border': 'none',
                        'color': '#1A1A1A',
                        'fontSize': '0.95rem',
                        'width': '100%',
                        'outline': 'none',
                        'paddingLeft': '0.75rem'
                    }
                )
            ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'gap': '0.75rem'})
        ], className='keyword-search-bar', style={
            'display': 'flex',
            'alignItems': 'center',
            'backgroundColor': '#FFFFFF',
            'padding': '0.75rem 1.5rem',
            'borderRadius': '8px',
            'border': '2px solid #E8ECEF',
            'marginBottom': '1rem',
            'gap': '1rem',
            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'
        }),

        # Filters and buttons row
        html.Div([
            html.Div([
                html.Div([
                    html.I(className='fas fa-utensils', id='cuisine-icon',
                           style={'cursor': 'pointer', 'color': '#003580'}, n_clicks=0),
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
                           style={'cursor': 'pointer', 'color': '#003580'}, n_clicks=0),
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
                html.I(id='filter-icon', className='fas fa-filter', style={'marginRight': '8px'}),
                'Filters'
            ], id='toggle-advanced-filters', className='btn-filter', n_clicks=0)
        ], className='search-container'),

        # Advanced filters panel (collapsible)
        html.Div([
            html.Div([
                # Price range filter
                html.Div([
                    html.Label('Price Range', style={'color': '#003580', 'fontWeight': 'bold', 'marginBottom': '0.5rem'}),
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
                'backgroundColor': '#F2F6FA',
                'padding': '1.5rem',
                'borderRadius': '8px',
                'border': '1px solid #E8ECEF',
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
               style={'fontSize': '3rem', 'color': '#003580'}),
        html.P('Loading restaurant details...',
               style={'color': '#1A1A1A', 'marginTop': '1rem', 'fontSize': '1.2rem'})
    ], style={
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'minHeight': '80vh',
        'backgroundColor': '#F2F6FA'
    })

def create_error_state(error_message):
    """錯誤狀態顯示（Error display with back button）"""
    return html.Div([
        html.I(className='fas fa-exclamation-triangle',
               style={'fontSize': '3rem', 'color': '#003580', 'marginBottom': '1rem'}),
        html.H2('Restaurant Not Found',
                style={'color': '#1A1A1A', 'marginBottom': '0.5rem'}),
        html.P(error_message,
               style={'color': '#555555', 'marginBottom': '2rem', 'fontSize': '1.1rem', 'fontWeight': '500'}),
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
        'backgroundColor': '#F2F6FA',
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
                    html.Img(
                        id='user-avatar-img-detail',
                        src=None,
                        style={
                            'width': '40px',
                            'height': '40px',
                            'borderRadius': '50%',
                            'objectFit': 'cover',
                            'display': 'none'
                        }
                    ),
                    html.I(
                        id='user-avatar-icon-detail',
                        className='fas fa-user',
                        style={'display': 'block'}
                    )
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
            ], style={'position': 'relative'})
        ], style={
            'maxWidth': '1400px',
            'margin': '0 auto',
            'padding': '1rem 2rem',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'space-between'
        })
    ], style={
        'backgroundColor': '#F2F6FA',
        'borderBottom': '1px solid #E8ECEF',
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
            stars.append(html.I(className='fas fa-star', style={'color': '#deb522', 'marginRight': '4px', 'textShadow': '1px 1px 3px rgba(0,0,0,0.5)'}))
        else:
            stars.append(html.I(className='far fa-star', style={'color': 'rgba(255, 255, 255, 0.5)', 'marginRight': '4px', 'textShadow': '1px 1px 3px rgba(0,0,0,0.5)'}))

    return html.Div([
        # 圖片畫廊（替換原本的單一圖片）
        create_image_gallery(),

        # 漸層遮罩 (subtle shadow for text readability)
        html.Div(style={
            'position': 'absolute',
            'bottom': '0',
            'left': '0',
            'right': '0',
            'height': '70%',
            'background': 'linear-gradient(to top, rgba(0, 0, 0, 0.6) 0%, rgba(0, 0, 0, 0.2) 70%, transparent 100%)',
            'pointerEvents': 'none'  # 讓遮罩不阻擋按鈕點擊
        }),

        # Hero 內容
        html.Div([
            html.H1(data.get('Name', 'Restaurant'), style={
                'color': '#FFFFFF',
                'fontSize': '3rem',
                'fontWeight': 'bold',
                'marginBottom': '0.5rem',
                'textShadow': '2px 2px 8px rgba(0,0,0,0.7)'
            }),
            html.Div(data.get('JapaneseName', ''), style={
                'color': '#FFFFFF',
                'fontSize': '1.5rem',
                'marginBottom': '1rem',
                'fontWeight': '500',
                'textShadow': '1px 1px 4px rgba(0,0,0,0.7)'
            }),
            html.Div([
                html.Div(stars + [
                    html.Span(f"{rating:.1f}", style={
                        'color': '#deb522',
                        'fontSize': '1.8rem',
                        'fontWeight': 'bold',
                        'marginLeft': '12px',
                        'textShadow': '1px 1px 3px rgba(0,0,0,0.5)'
                    })
                ], style={'marginBottom': '1rem'}),
                html.Div([
                    html.Span([
                        html.I(className='fas fa-utensils', style={'marginRight': '6px'}),
                        data.get('SecondCategory', data.get('FirstCategory', 'Restaurant'))
                    ], style={
                        'backgroundColor': 'rgba(255, 255, 255, 0.25)',
                        'backdropFilter': 'blur(10px)',
                        'border': '1.5px solid rgba(255, 255, 255, 0.5)',
                        'color': '#FFFFFF',
                        'padding': '8px 16px',
                        'borderRadius': '20px',
                        'marginRight': '10px',
                        'fontSize': '1rem',
                        'fontWeight': '500',
                        'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.2)'
                    }),
                    html.Span([
                        html.I(className='fas fa-yen-sign', style={'marginRight': '6px'}),
                        data.get('Price_Category', 'N/A')
                    ], style={
                        'backgroundColor': 'rgba(255, 255, 255, 0.25)',
                        'backdropFilter': 'blur(10px)',
                        'border': '1.5px solid rgba(255, 255, 255, 0.5)',
                        'color': '#FFFFFF',
                        'padding': '8px 16px',
                        'borderRadius': '20px',
                        'marginRight': '10px',
                        'fontSize': '1rem',
                        'fontWeight': '500',
                        'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.2)'
                    }),
                    html.Span([
                        html.I(className='fas fa-comment', style={'marginRight': '6px'}),
                        f"{data.get('ReviewNum', 0)} reviews"
                    ], style={
                        'backgroundColor': 'rgba(255, 255, 255, 0.25)',
                        'backdropFilter': 'blur(10px)',
                        'border': '1.5px solid rgba(255, 255, 255, 0.5)',
                        'color': '#FFFFFF',
                        'padding': '8px 16px',
                        'borderRadius': '20px',
                        'marginRight': '10px',
                        'fontSize': '1rem',
                        'fontWeight': '500',
                        'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.2)'
                    }),

                    html.Button([
                        html.I(className='fas fa-heart', style={'marginRight': '6px'}),
                        'Add to Favorites'
                    ], id='favorite-button', n_clicks=0, style={
                        'backgroundColor': 'rgba(255, 255, 255, 0.25)',
                        'backdropFilter': 'blur(10px)',
                        'border': '1.5px solid rgba(255, 255, 255, 0.5)',
                        'color': '#FFFFFF',
                        'padding': '8px 16px',
                        'borderRadius': '20px',
                        'fontSize': '1rem',
                        'fontWeight': '500',
                        'cursor': 'pointer',
                        'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.2)',
                        'transition': 'all 0.3s ease'
                    })
                ], style={
                    'display': 'flex', 
                    'alignItems': 'center',
                    'flexWrap': 'wrap'
                })
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
        html.H3('Location', style={'color': '#003580', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div([
            html.I(className='fas fa-map-marker-alt', style={'color': '#003580', 'marginRight': '12px', 'fontSize': '1.2rem'}),
            html.Span(data.get('Station', 'Not Available'), style={'color': '#1A1A1A', 'fontSize': '1.1rem'})
        ], style={'marginBottom': '1rem', 'display': 'flex', 'alignItems': 'center'}),
        html.Small(f"Coordinates: {lat:.6f}, {long:.6f}" if has_coords else "Coordinates not available",
                   style={'color': '#555555', 'fontSize': '0.9rem', 'fontWeight': '500'})
    ], style={
        'backgroundColor': '#F2F6FA',
        'border': '1.5px solid #D0D5DD',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem',
        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
    })

def create_pricing_section(data):
    """創建價格資訊區域"""
    dinner_price = data.get('DinnerPrice', 'Not Available')
    lunch_price = data.get('LunchPrice', 'Not Available')

    return html.Div([
        html.H3('Pricing', style={'color': '#003580', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div([
            html.I(className='fas fa-moon', style={'color': '#003580', 'marginRight': '12px', 'fontSize': '1.1rem'}),
            html.Span('Dinner: ', style={'color': '#555555', 'marginRight': '8px', 'fontSize': '1rem', 'fontWeight': '600'}),
            html.Span(dinner_price, style={'color': '#1A1A1A', 'fontSize': '1.1rem', 'fontWeight': '500'})
        ], style={'marginBottom': '0.8rem', 'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.I(className='fas fa-sun', style={'color': '#003580', 'marginRight': '12px', 'fontSize': '1.1rem'}),
            html.Span('Lunch: ', style={'color': '#555555', 'marginRight': '8px', 'fontSize': '1rem', 'fontWeight': '600'}),
            html.Span(lunch_price, style={'color': '#1A1A1A', 'fontSize': '1.1rem', 'fontWeight': '500'})
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={
        'backgroundColor': '#F2F6FA',
        'border': '1.5px solid #D0D5DD',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem',
        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
    })

def create_categories_section(data):
    """創建分類標籤區域"""
    first_category = data.get('FirstCategory', '')
    second_category = data.get('SecondCategory', '')

    categories = []
    if first_category:
        categories.append(html.Span(first_category, style={
            'backgroundColor': 'rgba(222, 181, 34, 0.1)',
            'border': '1px solid #003580',
            'color': '#003580',
            'padding': '8px 16px',
            'borderRadius': '20px',
            'marginRight': '10px',
            'fontSize': '1rem',
            'display': 'inline-block'
        }))
    if second_category and second_category != first_category:
        categories.append(html.Span(second_category, style={
            'backgroundColor': 'rgba(222, 181, 34, 0.1)',
            'border': '1px solid #003580',
            'color': '#003580',
            'padding': '8px 16px',
            'borderRadius': '20px',
            'fontSize': '1rem',
            'display': 'inline-block'
        }))

    if not categories:
        categories.append(html.Span('No categories available', style={'color': '#888888', 'fontSize': '1rem'}))

    return html.Div([
        html.H3('Categories', style={'color': '#003580', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div(categories)
    ], style={
        'backgroundColor': '#F2F6FA',
        'border': '1.5px solid #D0D5DD',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem',
        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
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
            html.H3('Map', style={'color': '#003580', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
            html.Div([
                html.I(className='fas fa-map-marker-alt', style={'fontSize': '3rem', 'color': '#555555', 'marginBottom': '1rem'}),
                html.P('Location coordinates not available', style={'color': '#555555', 'fontSize': '1rem', 'textAlign': 'center', 'fontWeight': '500'})
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'justifyContent': 'center',
                'minHeight': '200px'
            })
        ], style={
            'backgroundColor': '#F2F6FA',
            'border': '1px solid #E8ECEF',
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
                        'color': '#1A1A1A',
                        'fontSize': '0.95rem',
                        'fontWeight': '600',
                        'marginBottom': '4px'
                    }),
                    html.Div([
                        html.Span([
                            html.I(className='fas fa-star', style={'color': '#003580', 'fontSize': '0.75rem', 'marginRight': '4px'}),
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
                'backgroundColor': '#F2F6FA',
                'border': '1.5px solid #D0D5DD',
                'borderRadius': '8px',
                'marginBottom': '8px',
                'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.05)',
                'transition': 'border-color 0.3s',
                'cursor': 'pointer'
            }, className='nearby-restaurant-card',
            id={'type': 'nearby-restaurant-card', 'index': nearby['Restaurant_ID']},
            n_clicks=0)
        ])
        nearby_cards.append(card)

    return html.Div([
        html.H3('Location & Map', style={'color': '#003580', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div([
            html.I(className='fas fa-map-marker-alt', style={'color': '#003580', 'marginRight': '8px'}),
            f"{station}, Kyoto"
        ], style={'color': '#555555', 'marginBottom': '1rem', 'fontSize': '0.95rem', 'fontWeight': '500'}),

        # Google Map
        map_component,

        # Map action buttons
        html.Div([
            html.A(
                [
                    html.I(className='fas fa-external-link-alt', style={'marginRight': '6px'}),
                    'View on Google Maps'
                ],
                href=f"https://www.google.com/maps/search/?api=1&query={lat},{long}",
                target="_blank",
                style={
                    'display': 'inline-block',
                    'padding': '8px 16px',
                    'backgroundColor': '#4285f4',
                    'color': 'white',
                    'textDecoration': 'none',
                    'borderRadius': '6px',
                    'fontSize': '0.9rem',
                    'transition': 'background-color 0.3s'
                }
            ),
            html.A(
                [
                    html.I(className='fas fa-directions', style={'marginRight': '6px'}),
                    'Get Directions'
                ],
                href=f"https://www.google.com/maps/dir/?api=1&destination={lat},{long}",
                target="_blank",
                style={
                    'display': 'inline-block',
                    'padding': '8px 16px',
                    'backgroundColor': '#34A853',
                    'color': 'white',
                    'textDecoration': 'none',
                    'borderRadius': '6px',
                    'fontSize': '0.9rem',
                    'transition': 'background-color 0.3s',
                    'marginLeft': '10px'
                }
            )
        ], style={'marginTop': '12px'}),

        # 附近餐廳列表
        html.Div([
            html.H4([
                html.I(className='fas fa-utensils', style={'marginRight': '8px', 'color': '#003580'}),
                f'Nearby Restaurants ({len(nearby_restaurants)})'
            ], style={'color': '#1A1A1A', 'fontSize': '1.1rem', 'marginBottom': '1rem', 'marginTop': '2rem'}),
            html.Div(nearby_cards)
        ]) if nearby_restaurants else html.Div()

    ], style={
        'backgroundColor': '#F2F6FA',
        'border': '1.5px solid #D0D5DD',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
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
                stars.append(html.I(className='fas fa-star', style={'color': '#003580', 'marginRight': '3px', 'fontSize': '0.9rem'}))
            else:
                stars.append(html.I(className='far fa-star', style={'color': '#555555', 'marginRight': '3px', 'fontSize': '0.9rem'}))

        return html.Div([
            html.Span(label, style={'color': '#555555', 'minWidth': '80px', 'fontSize': '1rem', 'fontWeight': '600'}),
            html.Div(stars, style={'display': 'flex', 'alignItems': 'center', 'flex': '1'}),
            html.Span(f"{rating:.1f}", style={'color': '#1A1A1A', 'fontWeight': 'bold', 'marginLeft': '12px', 'fontSize': '1.1rem'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '0.8rem'})

    return html.Div([
        html.H3('Ratings Breakdown', style={'color': '#003580', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        create_rating_row('Overall', data.get('TotalRating', 0)),
        create_rating_row('Dinner', data.get('DinnerRating', 0)),
        create_rating_row('Lunch', data.get('LunchRating', 0))
    ], style={
        'backgroundColor': '#F2F6FA',
        'border': '1.5px solid #D0D5DD',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem',
        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
    })

def create_statistics_section(data):
    """創建統計資訊區域"""
    # Count actual reviews from the reviews list instead of using ReviewNum field
    reviews = data.get('reviews', []) if isinstance(data, dict) else []
    review_num = len(reviews)
    rating_category = data.get('Rating_Category', 'N/A')

    return html.Div([
        html.H3('Statistics', style={'color': '#003580', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        html.Div([
            html.I(className='fas fa-comment', style={'color': '#003580', 'marginRight': '12px', 'fontSize': '1.5rem'}),
            html.Div([
                html.Div(f"{review_num:,}", style={'color': '#1A1A1A', 'fontSize': '1.8rem', 'fontWeight': 'bold'}),
                html.Div('Total Reviews', style={'color': '#555555', 'fontSize': '0.9rem', 'fontWeight': '600'})
            ])
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '1.5rem'}),
        html.Div([
            html.I(className='fas fa-award', style={'color': '#003580', 'marginRight': '12px', 'fontSize': '1.5rem'}),
            html.Div([
                html.Div(rating_category, style={'color': '#1A1A1A', 'fontSize': '1.3rem', 'fontWeight': 'bold'}),
                html.Div('Rating Category', style={'color': '#555555', 'fontSize': '0.9rem', 'fontWeight': '600'})
            ])
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={
        'backgroundColor': '#F2F6FA',
        'border': '1.5px solid #D0D5DD',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem',
        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
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

    # Create Plotly bar chart for visibility with enhanced interactivity
    fig = px.bar(
        x=ratings,
        y=values,
        labels={'x': 'Stars', 'y': 'Count'},
        title='Ratings distribution',
        text=values,
        height=360
    )

    # Enhanced styling with hover and click effects
    fig.update_traces(
        marker_color='#FBC02D',
        marker_line_color='#ffffff',
        marker_line_width=0,
        hovertemplate='<b>%{x} Stars</b><br>Count: %{y}<br><i>Click to view reviews</i><extra></extra>',
        hoverlabel=dict(
            bgcolor='#2a2a2a',
            font_size=14,
            font_family='Segoe UI, Arial',
            font_color='#ffffff',
            bordercolor='#003580'
        )
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title={
            'text': 'Ratings distribution - <i>Click on any bar to view reviews</i>',
            'x': 0.02,
            'xanchor': 'left',
            'font': {'color': '#1A1A1A', 'size': 16}
        },
        xaxis=dict(
            tickfont=dict(color='#ffffff', size=12),
            title=dict(text='Stars', font=dict(color='#003580', size=14))
        ),
        yaxis=dict(
            tickfont=dict(color='#ffffff', size=12),
            title=dict(text='Count', font=dict(color='#003580', size=14))
        ),
        margin=dict(l=60, r=20, t=60, b=60),
        hovermode='closest',
        transition=dict(duration=500, easing='cubic-in-out'),
        uirevision='constant'  # Maintain zoom/pan state across updates
    )

    comments_area = html.Div(id='reviews-comments', children=[
        html.Div('Click a star bar to show comments', style={'color': '#888888', 'fontStyle': 'italic'})
    ], style={
        'marginTop': '1rem',
        'color': '#1A1A1A',
        'minHeight': '80px',
        'maxHeight': '260px',
        'overflowY': 'auto',
        'transition': 'all 0.3s ease'
    })

    return html.Div([
        html.H3('Reviews', style={'color': '#003580', 'marginBottom': '1rem', 'fontSize': '1.5rem', 'fontWeight': 'bold'}),
        dcc.Store(id='selected-rating-store', data=None),
        html.Div([
            dcc.Graph(
                id='ratings-bar-chart',
                figure=fig,
                config={
                    'displayModeBar': False,
                    'responsive': True
                },
                style={'cursor': 'pointer', 'height': '360px'}
            )
        ], style={'minHeight': '360px', 'maxHeight': '360px', 'overflow': 'hidden'}),
        comments_area
    ], style={
        'backgroundColor': '#F2F6FA',
        'border': '1.5px solid #D0D5DD',
        'borderRadius': '12px',
        'padding': '1.5rem',
        'marginBottom': '1.5rem',
        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
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
    ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})

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


def create_trip_layout():
    """創建行程規劃頁面 (左右欄位設計)"""
    return html.Div([
        # Header
        html.Div([
            html.Button([html.I(className='fas fa-arrow-left'), ' Back'], id={'type': 'back-btn', 'index': 'planner'}, className='btn-secondary'),
            html.H1("Trip Planner", style={'color': '#003580', 'marginLeft': '2rem'})
        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '1rem 2rem', 'backgroundColor': '#fff', 'borderBottom': '1px solid #eee'}),

        # Main Workspace
        dbc.Row([
            # --- LEFT COLUMN: Source Items ---
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Tabs([
                            dbc.Tab(label="My Favorites", tab_id="tab-plan-fav", label_style={"fontWeight": "bold"}),
                            dbc.Tab(label="Recommendations", tab_id="tab-plan-rec", label_style={"fontWeight": "bold"}),
                        ], id="planner-tabs", active_tab="tab-plan-fav")
                    ]),
                    dbc.CardBody([
                        # 這裡顯示可加入的項目
                        html.Div(id="planner-source-list", style={'height': '70vh', 'overflowY': 'auto', 'paddingRight': '10px'})
                    ])
                ], style={'height': '80vh', 'border': 'none', 'boxShadow': '0 4px 12px rgba(0,0,0,0.05)'})
            ], width=4, style={'paddingRight': '0'}),

            # --- RIGHT COLUMN: Itinerary ---
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("My Itinerary", className="m-0", style={'color': '#003580'}),
                        html.Small("Click 'Add' on items from the left to populate your trip", className="text-muted")
                    ], style={'backgroundColor': '#f8f9fa'}),
                    dbc.CardBody([
                        # 這裡顯示已加入的行程
                        html.Div(id="planner-itinerary-view", style={'minHeight': '60vh'}),
                        
                        html.Hr(),
                        dbc.Button("+ Add Day", id="add-day-btn", color="secondary", outline=True, size="sm", className="me-2"),
                        dbc.Button("Save Trip Plan", id="save-trip-plan-btn", color="primary", className="float-end")
                    ], style={'height': '75vh', 'overflowY': 'auto'})
                ], style={'height': '80vh', 'border': 'none', 'boxShadow': '0 4px 12px rgba(0,0,0,0.05)'})
            ], width=8)
        ], style={'padding': '2rem', 'maxWidth': '1600px', 'margin': '0 auto'}),
        
        # 暫存行程資料
        dcc.Store(id='trip-plan-data', data={'days': [{'day': 1, 'items': []}]}) 

    ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})

def create_hotel_card(hotel, id_type='hotel-card', is_favorite=False): # [新增] is_favorite 參數
    """創建旅館卡片 (支援自定義 ID 類型與收藏狀態)"""
    types_text = ', '.join(hotel['Types'][:2]) if isinstance(hotel['Types'], list) and hotel['Types'] else 'Hotel'
    rating = hotel.get('Rating', 0)
    rating_text = f"{rating:.1f}" if rating is not None else "N/A"

    # 決定愛心樣式
    heart_icon = "fas fa-heart" if is_favorite else "far fa-heart"
    heart_color = "#ff4757" if is_favorite else "white"

    card_content = html.Div([
        # Image section
        html.Div([
            html.Img(src='/assets/food_dirtyrice.png', className='card-image'),
            
            # [新增] 愛心按鈕
            html.Div(
                html.I(className=heart_icon, style={'color': heart_color, 'fontSize': '1.2rem'}),
                id={'type': 'fav-btn', 'item_type': 'Hotel', 'index': hotel['Hotel_ID']},
                n_clicks=0,
                style={
                    'position': 'absolute', 'top': '10px', 'right': '10px', 
                    'background': 'rgba(0,0,0,0.5)', 'borderRadius': '50%', 
                    'width': '35px', 'height': '35px', 'display': 'flex', 
                    'alignItems': 'center', 'justifyContent': 'center', 
                    'cursor': 'pointer', 'zIndex': '10'
                }
            )
        ], className='card-image-section', style={'position': 'relative'}),

        html.Div([
            html.Div(hotel['HotelName'], className='card-title'),
            html.Div(types_text, className='card-subtitle'),
            html.Div([
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.Span(rating_text)
            ], className='card-rating'),
            html.Div([
                html.I(className='fas fa-map-marker-alt', style={'marginRight': '5px', 'fontSize': '0.8rem'}),
                html.Span(hotel['Address'][:30] + '...' if len(hotel['Address']) > 30 else hotel['Address'],
                          style={'fontSize': '0.75rem', 'color': '#888'})
            ], style={'marginTop': '5px'})
        ], className='card-content-section')
    ], className='destination-card')

    return html.Div(
        card_content,
        id={'type': id_type, 'index': hotel['Hotel_ID']},
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
    """創建旅館搜尋欄 (與餐廳搜尋相同的佈局)"""
    return html.Div([
        # Keyword search bar (separate row for full width) - Row 1
        html.Div([
            html.Div([
                html.I(className='fas fa-search', style={'color': '#003580', 'fontSize': '1.2rem'}),
                dcc.Input(
                    id='search-hotel',
                    type='text',
                    value='',
                    placeholder='Search hotels by name (English or Japanese)...',
                    className='search-input',
                    debounce=False,  # 即時搜尋
                    style={
                        'background': 'transparent',
                        'border': 'none',
                        'color': '#1A1A1A',
                        'fontSize': '0.95rem',
                        'width': '100%',
                        'outline': 'none',
                        'paddingLeft': '0.75rem'
                    }
                )
            ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'gap': '0.75rem'})
        ], className='keyword-search-bar', style={
            'display': 'flex',
            'alignItems': 'center',
            'backgroundColor': '#FFFFFF',
            'padding': '0.75rem 1.5rem',
            'borderRadius': '8px',
            'border': '2px solid #E8ECEF',
            'marginBottom': '1rem',
            'gap': '1rem',
            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'
        }),

        # Filters row - Row 2 (no search button, auto-search like restaurants)
        html.Div([
            html.Div([
                html.Div([
                    html.I(className='fas fa-hotel', id='hotel-type-icon',
                           style={'cursor': 'pointer', 'color': '#003580'}, n_clicks=0),
                    html.Span(id='hotel-type-selected-text',
                             children='Hotel Type',
                             style={'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'})
                ], id='hotel-type-trigger', style={'display': 'flex', 'alignItems': 'center'}, n_clicks=0),

                # Hidden dropdown list
                html.Div([
                    html.Div(create_hotel_type_options(),
                            style={'maxHeight': '300px', 'overflowY': 'auto'})
                ], id='hotel-type-dropdown-menu', className='custom-dropdown-menu',
                   style={'display': 'none'})
            ], className='search-input-group', style={'flex': '1', 'minWidth': '200px', 'position': 'relative'})
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
                        html.Img(
                            id='user-avatar-img-hotel-detail',
                            src=None,
                            style={
                                'width': '40px',
                                'height': '40px',
                                'borderRadius': '50%',
                                'objectFit': 'cover',
                                'display': 'none'
                            }
                        ),
                        html.I(
                            id='user-avatar-icon-hotel-detail',
                            className='fas fa-user',
                            style={'display': 'block'}
                        )
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
                        ], className='dropdown-item', id='menu-logout-hotel-detail', n_clicks=0)
                    ], id='user-dropdown-hotel-detail', className='user-dropdown')
                ], style={'position': 'relative'})

            ], style={
                'maxWidth': '1400px',
                'margin': '0 auto',
                'padding': '1rem 2rem',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'space-between'
            })
        ], style={
            'backgroundColor': '#F2F6FA',
            'borderBottom': '1px solid #E8ECEF',
            'position': 'sticky',
            'top': '0',
            'zIndex': '1000'
        }),
        
        # 主要內容容器 (將由 callback 填充 create_hotel_detail_content 的結果)
        html.Div(id='hotel-detail-content', children=[
            create_loading_state() # 預設顯示載入中
        ])
    ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})

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
            stars.append(html.I(className='fas fa-star', style={'color': '#deb522', 'marginRight': '4px', 'textShadow': '1px 1px 3px rgba(0,0,0,0.5)'}))
        else:
            stars.append(html.I(className='far fa-star', style={'color': 'rgba(255, 255, 255, 0.5)', 'marginRight': '4px', 'textShadow': '1px 1px 3px rgba(0,0,0,0.5)'}))
    
    # 處理類型列表
    types = hotel_data.get('Types', [])
    if isinstance(types, list):
        types_text = ', '.join(types)
    else:
        types_text = 'Hotel'
    
    return html.Div([
        # Hero 區域 (大圖)
        html.Div([
            # 圖片畫廊（替換原本的單一圖片）
            create_image_gallery(),

            # 漸層遮罩 (subtle shadow for text readability)
            html.Div(style={
                'position': 'absolute',
                'bottom': '0',
                'left': '0',
                'right': '0',
                'height': '70%',
                'background': 'linear-gradient(to top, rgba(0, 0, 0, 0.6) 0%, rgba(0, 0, 0, 0.2) 70%, transparent 100%)',
                'pointerEvents': 'none'
            }),
            html.Div([
                html.H1(hotel_data.get('HotelName', 'Hotel'), style={
                    'color': '#FFFFFF',
                    'fontSize': '3rem',
                    'fontWeight': 'bold',
                    'marginBottom': '0.5rem',
                    'textShadow': '2px 2px 8px rgba(0,0,0,0.7)'
                }),
                html.Div([
                    html.Div(stars + [
                        html.Span(f"{rating:.1f}", style={
                            'color': '#deb522',
                            'fontSize': '1.8rem',
                            'fontWeight': 'bold',
                            'marginLeft': '12px',
                            'textShadow': '1px 1px 3px rgba(0,0,0,0.5)'
                        })
                    ], style={'marginBottom': '1rem'}),
                    html.Div([
                        html.Span([
                            html.I(className='fas fa-hotel', style={'marginRight': '6px'}),
                            types_text
                        ], style={
                            'backgroundColor': 'rgba(255, 255, 255, 0.25)',
                            'backdropFilter': 'blur(10px)',
                            'border': '1.5px solid rgba(255, 255, 255, 0.5)',
                            'color': '#FFFFFF',
                            'padding': '8px 16px',
                            'borderRadius': '20px',
                            'marginRight': '10px',
                            'fontSize': '1rem',
                            'fontWeight': '500',
                            'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.2)'
                        }),
                        html.Span([
                            html.I(className='fas fa-comment', style={'marginRight': '6px'}),
                            f"{int(hotel_data.get('UserRatingsTotal', 0))} reviews"
                        ], style={
                            'backgroundColor': 'rgba(255, 255, 255, 0.25)',
                            'backdropFilter': 'blur(10px)',
                            'border': '1.5px solid rgba(255, 255, 255, 0.5)',
                            'color': '#FFFFFF',
                            'padding': '8px 16px',
                            'borderRadius': '20px',
                            'marginRight': '10px',
                            'fontSize': '1rem',
                            'fontWeight': '500',
                            'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.2)'
                        }),
                        html.Button([
                            html.I(className='fas fa-heart', style={'marginRight': '6px'}),
                            'Add to Favorites'
                        ], id='favorite-button', n_clicks=0, style={
                            'backgroundColor': 'rgba(255, 255, 255, 0.25)',
                            'backdropFilter': 'blur(10px)',
                            'border': '1.5px solid rgba(255, 255, 255, 0.5)',
                            'color': '#FFFFFF',
                            'padding': '8px 16px',
                            'borderRadius': '20px',
                            'fontSize': '1rem',
                            'fontWeight': '500',
                            'cursor': 'pointer',
                            'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.2)',
                            'transition': 'all 0.3s ease'
                        })
                    ], style={
                        'display': 'flex', 
                        'alignItems': 'center',
                        'flexWrap': 'wrap'
                    })
                ])
            ], style={
                'position': 'absolute',
                'bottom': '3rem',
                'left': '2rem',
                'right': '2rem',
                'maxWidth': '1400px',
                'margin': '0 auto',
                'pointerEvents': 'none'
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
                            html.H3('Location', style={'color': '#003580', 'marginBottom': '1rem'}),
                            html.Div([
                                html.I(className='fas fa-map-marker-alt', style={'marginRight': '12px', 'color': '#003580'}),
                                html.Span(hotel_data.get('Address', 'N/A'))
                            ], style={'color': '#1A1A1A', 'marginBottom': '1rem'}),
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
                            'backgroundColor': '#F2F6FA',
                            'border': '1px solid #E8ECEF',
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

# --- Attractions UI Components ---

def create_attraction_card(attr, id_type='attraction-card', is_favorite=False): # [新增] 參數
    """建立景點小卡 (樣式與 Hotel/Restaurant 完全一致)"""
    # 處理 Price Level
    price_level = attr.get('PriceLevel')
    price_display = ''
    if price_level and pd.notna(price_level):
        try:
            p_val = float(price_level)
            price_display = '💰' * int(p_val)
        except: pass
    
    # 決定愛心樣式
    heart_icon = "fas fa-heart" if is_favorite else "far fa-heart"
    heart_color = "#ff4757" if is_favorite else "white"

    card_content = html.Div([
        # 上半部：圖片區
        html.Div([
            html.Img(src='/assets/food_dirtyrice.png', className='card-image'),
            
            # [新增] 愛心按鈕
            html.Div(
                html.I(className=heart_icon, style={'color': heart_color, 'fontSize': '1.2rem'}),
                id={'type': 'fav-btn', 'item_type': 'Attraction', 'index': attr['ID']},
                n_clicks=0,
                style={
                    'position': 'absolute', 'top': '10px', 'right': '10px', 
                    'background': 'rgba(0,0,0,0.5)', 'borderRadius': '50%', 
                    'width': '35px', 'height': '35px', 'display': 'flex', 
                    'alignItems': 'center', 'justifyContent': 'center', 
                    'cursor': 'pointer', 'zIndex': '10'
                }
            )
        ], className='card-image-section', style={'position': 'relative'}),
        
        # 下半部：內容區
        html.Div([
            html.Div(attr['Name'], className='card-title'),
            html.Div([
                html.Span(attr.get('Type', 'Spot'), className='card-subtitle'),
                html.Span(price_display, style={'marginLeft': '10px', 'color': '#FBC02D', 'fontSize': '0.9rem'})
            ], style={'marginBottom': '0.5rem'}),
            
            html.Div([
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.I(className='fas fa-star'),
                html.Span(f"{attr.get('Rating', 0):.1f}", style={'marginLeft': '5px'})
            ], className='card-rating'),
            
            html.Div([
                html.I(className='fas fa-map-marker-alt', style={'marginRight': '5px', 'fontSize': '0.8rem'}),
                html.Span(str(attr.get('Address', ''))[:30] + '...', style={'fontSize': '0.75rem', 'color': '#888'})
            ], style={'marginTop': '5px'})
            
        ], className='card-content-section') 
    ], className='destination-card')

    return html.Div(
        card_content,
        id={'type': id_type, 'index': attr['ID']},
        style={'cursor': 'pointer'},
        n_clicks=0
    )

def create_attraction_search_bar():
    """創建優化的景點搜尋欄（帶篩選功能）"""
    return html.Div([
        # Keyword search bar (separate row for full width)
        html.Div([
            html.Div([
                html.I(className='fas fa-search', style={'color': '#003580', 'fontSize': '1.2rem'}),
                dcc.Input(
                    id='search-attraction',
                    type='text',
                    value='',
                    placeholder='Search attractions by name (shrines, temples, parks, etc.)...',
                    className='search-input',
                    debounce=False,
                    style={
                        'background': 'transparent',
                        'border': 'none',
                        'color': '#1A1A1A',
                        'fontSize': '0.95rem',
                        'width': '100%',
                        'outline': 'none',
                        'paddingLeft': '0.75rem'
                    }
                )
            ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'gap': '0.75rem'})
        ], className='keyword-search-bar', style={
            'display': 'flex',
            'alignItems': 'center',
            'backgroundColor': '#FFFFFF',
            'padding': '0.75rem 1.5rem',
            'borderRadius': '8px',
            'border': '2px solid #E8ECEF',
            'marginBottom': '1rem',
            'gap': '1rem',
            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'
        }),

        # Filters and buttons row
        html.Div([
            html.Div([
                html.Div([
                    html.I(className='fas fa-torii-gate', id='attraction-type-icon',
                           style={'cursor': 'pointer', 'color': '#003580'}, n_clicks=0),
                    html.Span(id='attraction-type-selected-text',
                             children='Attraction Type',
                             style={'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'})
                ], id='attraction-type-trigger', style={'display': 'flex', 'alignItems': 'center'}, n_clicks=0),

                # Hidden dropdown list
                html.Div([
                    html.Div(create_attraction_type_options(),
                            style={'maxHeight': '300px', 'overflowY': 'auto'})
                ], id='attraction-type-dropdown-menu', className='custom-dropdown-menu',
                   style={'display': 'none'})
            ], className='search-input-group', style={'flex': '1', 'minWidth': '200px', 'position': 'relative'}),

            html.Div([
                html.Div([
                    html.I(className='fas fa-star', id='attraction-rating-icon',
                           style={'cursor': 'pointer', 'color': '#003580'}, n_clicks=0),
                    html.Span(id='attraction-rating-selected-text',
                             children='Rating',
                             style={'cursor': 'pointer', 'marginLeft': '10px', 'color': '#888888'})
                ], id='attraction-rating-trigger', style={'display': 'flex', 'alignItems': 'center'}, n_clicks=0),

                # Hidden dropdown list
                html.Div([
                    html.Div(create_attraction_rating_options(),
                            style={'maxHeight': '300px', 'overflowY': 'auto'})
                ], id='attraction-rating-dropdown-menu', className='custom-dropdown-menu',
                   style={'display': 'none'})
            ], className='search-input-group', style={'flex': '1', 'minWidth': '200px', 'position': 'relative'})
        ], className='search-container')
    ], style={'width': '100%'})

def create_attraction_list_page():
    """建立景點列表頁 (樣式與餐廳列表一致)"""
    return html.Div([
        # ===== Header with back button =====
        html.Div([
            html.Div([
                # Back button and title
                html.Div([
                    html.Button([
                        html.I(className='fas fa-arrow-left'),
                        html.Span('Back', style={'marginLeft': '8px'})
                    ], id={'type': 'back-btn', 'index': 'attraction-list'}, className='btn-back', n_clicks=0),
                    html.H1('Attraction Directory', style={
                        'color': '#003580',
                        'marginLeft': '2rem',
                        'fontSize': '2rem',
                        'fontWeight': 'bold'
                    })
                ], style={'display': 'flex', 'alignItems': 'center'}),

                # User Avatar
                html.Div([
                    html.Div([
                        html.Img(
                            id='user-avatar-img-attraction-list',
                            src=None,
                            style={
                                'width': '40px',
                                'height': '40px',
                                'borderRadius': '50%',
                                'objectFit': 'cover',
                                'display': 'none'
                            }
                        ),
                        html.I(
                            id='user-avatar-icon-attraction-list',
                            className='fas fa-user',
                            style={'display': 'block'}
                        )
                    ], className='user-avatar', id='user-avatar-attraction-list', n_clicks=0),

                    # Dropdown Menu
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-user-circle'),
                            html.Span('Profile')
                        ], className='dropdown-item', id='dropdown-profile-attraction-list', n_clicks=0),
                        html.Div([
                            html.I(className='fas fa-sign-out-alt'),
                            html.Span('Logout')
                        ], className='dropdown-item', id='menu-logout-attraction-list', n_clicks=0),
                    ], id='user-dropdown-attraction-list', className='user-dropdown')
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
            'backgroundColor': '#F2F6FA',
            'borderBottom': '1px solid #E8ECEF',
            'position': 'sticky',
            'top': '0',
            'zIndex': '1000'
        }),

        # ===== Search and Filter Section =====
        html.Div([
            html.Div([
                # Search bar
                create_attraction_search_bar(),

                # Search stats
                html.Div(id='attraction-search-stats', style={
                    'color': '#555555',
                    'fontSize': '0.95rem',
                    'marginTop': '1rem',
                    'fontWeight': '500'
                })
            ], style={
                'maxWidth': '1000px',
                'margin': '0 auto'
            })
        ], style={
            'backgroundColor': '#F2F6FA',
            'padding': '2rem',
            'borderBottom': '1px solid #222'
        }),

        # ===== Attraction Grid =====
        html.Div([
            html.Div(id='attraction-grid', className='restaurant-list-grid')
        ], style={
            'backgroundColor': '#F2F6FA',
            'padding': '2rem',
            'minHeight': '60vh'
        }),

        # ===== Pagination Controls =====
        html.Div(id='attraction-pagination-controls', style={
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center',
            'gap': '0.5rem',
            'padding': '2rem',
            'backgroundColor': '#F2F6FA'
        }),

    ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})

def create_attraction_detail_page(attr_id):
    """建立景點詳細頁 (直接載入模式)"""
    # 1. 直接在這裡抓資料！
    print(f"DEBUG: Fetching data directly for Attraction ID: {attr_id}")
    data = get_attraction_by_id(attr_id)
    
    # 2. 生成內容
    if data:
        content = create_attraction_detail_content(data)
    else:
        content = create_error_state("Attraction not found in database")

    return html.Div([
        # Header (保持不變)
        html.Div([
            html.Div([
                html.Button([html.I(className='fas fa-arrow-left', style={'marginRight': '8px'}), 'Back'], 
                            id='attraction-detail-back-btn', className='btn-secondary', n_clicks=0, style={'marginRight': 'auto'}),
                
                # User Avatar
                html.Div([
                    html.Div([
                        html.Img(id='user-avatar-img-attraction-detail', src=None, style={'width': '40px', 'height': '40px', 'borderRadius': '50%', 'objectFit': 'cover', 'display': 'none'}),
                        html.I(id='user-avatar-icon-attraction-detail', className='fas fa-user', style={'display': 'block'})
                    ], id='user-avatar-attraction-detail', className='user-avatar', n_clicks=0),
                    # Dropdown
                    html.Div([
                        html.Div([html.I(className='fas fa-user-circle'), html.Span('Profile')], className='dropdown-item', id='menu-profile-attraction-detail', n_clicks=0),
                        html.Div([html.I(className='fas fa-sign-out-alt'), html.Span('Logout')], className='dropdown-item', id='menu-logout-attraction-detail', n_clicks=0)
                    ], id='user-dropdown-attraction-detail', className='user-dropdown')
                ], style={'position': 'relative'})
            ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '1rem 2rem', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'})
        ], style={'backgroundColor': '#F2F6FA', 'borderBottom': '1px solid #E8ECEF', 'position': 'sticky', 'top': '0', 'zIndex': '1000'}),

        # 3. 直接放入內容 (不再顯示 Loading)
        html.Div(id='attraction-detail-content', children=[content])

    ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})

def create_attraction_detail_content(data):
    """建立景點詳細內容 (包含超強防呆機制)"""
    # 1. 基礎檢查
    if not data or 'error' in data:
        return create_error_state("Attraction not found")

    # 2. 安全地處理資料 (防止 None/NaN 導致崩潰)
    name = data.get('Name', 'Unknown Spot')
    attr_type = data.get('Type', 'Spot')
    address = data.get('Address', 'Address not available')
    
    # --- [關鍵修正] 安全轉換數值 ---
    try:
        # 處理評分 (若為 None 轉為 0.0)
        raw_rating = data.get('Rating')
        rating = round(float(raw_rating), 1) if pd.notna(raw_rating) else 0.0
        
        # 處理評論數 (若為 None 轉為 0)
        raw_reviews = data.get('UserRatingsTotal')
        review_count = int(float(raw_reviews)) if pd.notna(raw_reviews) else 0
        
        # 處理經緯度
        lat = data.get('Lat')
        lng = data.get('Lng')
        
        # 處理價格 (PriceLevel)
        price_level = data.get('PriceLevel')
        price_text = "Free / Unknown"
        if pd.notna(price_level):
            try:
                p_val = int(float(price_level))
                if p_val > 0:
                    price_text = "💰" * p_val
            except:
                pass
    except Exception as e:
        print(f"Error parsing attraction data: {e}")
        return create_error_state(f"Data Error: {e}")

    return html.Div([
        # Hero Image Area
        html.Div([
            html.Img(src='/assets/food_dirtyrice.png', style={'width':'100%', 'height':'100%', 'objectFit':'cover', 'position': 'absolute', 'top': '0', 'left': '0'}),
            html.Div(style={'position': 'absolute', 'bottom': '0', 'left': '0', 'right': '0', 'height': '70%', 'background': 'linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 100%)'}),
            html.Div([
                html.H1(name, style={'color': '#fff', 'fontSize': '3rem', 'fontWeight': 'bold', 'textShadow': '2px 2px 4px rgba(0,0,0,0.8)', 'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span(attr_type, style={'backgroundColor': 'rgba(255,255,255,0.2)', 'backdropFilter': 'blur(5px)', 'color': '#fff', 'padding': '5px 15px', 'borderRadius': '20px', 'marginRight': '10px', 'border': '1px solid rgba(255,255,255,0.5)'}),
                    html.Span(f"{rating} ★ ({review_count} reviews)", style={'color': '#FBC02D', 'fontSize': '1.2rem', 'fontWeight': 'bold', 'textShadow': '1px 1px 2px rgba(0,0,0,0.8)'})
                ])
            ], style={'position': 'absolute', 'bottom': '3rem', 'left': '2rem', 'maxWidth': '1200px'})
        ], style={'position': 'relative', 'height': '50vh', 'minHeight': '400px', 'overflow': 'hidden'}),

        # Info Grid
        html.Div([
            html.Div([
                html.H3("Information", style={'color': '#003580', 'marginBottom': '1rem'}),
                html.Div([
                    html.P([html.I(className='fas fa-map-marker-alt', style={'marginRight':'12px', 'color':'#003580'}), str(address)], style={'color': '#1A1A1A', 'fontSize': '1.1rem', 'marginBottom': '0.8rem'}),
                    html.P([html.I(className='fas fa-tag', style={'marginRight':'12px', 'color':'#003580'}), f"Type: {attr_type}"], style={'color': '#555', 'marginBottom': '0.8rem'}),
                    html.P([html.I(className='fas fa-yen-sign', style={'marginRight':'12px', 'color':'#003580'}), f"Price Level: {price_text}"], style={'color': '#555'}),
                ], style={'backgroundColor': '#fff', 'padding': '1.5rem', 'borderRadius': '12px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.08)', 'border': '1.5px solid #D0D5DD', 'marginBottom': '2rem'}),
                
                html.H3("Location", style={'color': '#003580', 'marginBottom': '1rem'}),
                html.Div([
                     html.Iframe(
                        src=f"https://www.google.com/maps?q={lat},{lng}&z=15&output=embed",
                        style={'width': '100%', 'height': '300px', 'border': 'none', 'borderRadius': '8px'}
                    )
                ], style={'backgroundColor': '#fff', 'padding': '1rem', 'borderRadius': '12px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.08)', 'border': '1.5px solid #D0D5DD'})
            ], style={'flex': '1', 'minWidth': '300px'}),
            
            # 右側區塊
            html.Div([
                html.H3("Overview", style={'color': '#003580', 'marginBottom': '1rem'}),
                html.Div([
                    html.P(f"Welcome to {name}. Experience the rich history and culture of Kyoto at this location.", style={'color': '#555', 'lineHeight': '1.6'}),
                    html.P("Check the map for exact location and plan your visit!", style={'color': '#555', 'lineHeight': '1.6'})
                ], style={'backgroundColor': '#fff', 'padding': '2rem', 'borderRadius': '12px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.08)', 'border': '1.5px solid #D0D5DD'})
            ], style={'flex': '1', 'minWidth': '300px'})
        ], style={'display': 'flex', 'gap': '2rem', 'maxWidth': '1400px', 'margin': '0 auto', 'padding': '3rem 2rem', 'flexWrap': 'wrap'})
    ])

def create_restaurant_map_chart():
    """Creates a mapbox scatter plot of all restaurants."""
    try:
        # [防呆] 嘗試讀取資料
        df = get_all_restaurants()
        # 如果讀出來是空的，或發生錯誤，回傳空圖表
        if df is None or df.empty:
            raise ValueError("No data returned from database")

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
                bgcolor='rgba(0, 53, 128, 0.5)',
                font=dict(color='white')
            ),
            clickmode='event+select',
            hoverdistance=20
        )
        fig.update_traces(
            hovertemplate='<b>%{hovertext}</b><br>' +
                          'Rating: %{customdata[1]}<br>' +
                          '<i>Click to view details</i><extra></extra>',
            marker=dict(size=12, opacity=0.9),
            hoverlabel=dict(bgcolor='#003580', font_size=14, font_family='Arial, sans-serif')
        )
        return dcc.Graph(
            id='restaurant-map-graph',
            figure=fig,
            config={'displayModeBar': True, 'scrollZoom': True, 'doubleClick': 'reset', 'modeBarButtonsToRemove': ['lasso2d', 'select2d']}
        )

    except Exception as e:
        print(f"⚠️ Warning: Could not load Restaurant Map. Error: {e}")
        # 回傳一個空白圖表，避免 App 崩潰
        fig = go.Figure()
        fig.update_layout(
            title="Map Data Unavailable (Please check database)",
            xaxis={'visible': False}, yaxis={'visible': False}
        )
        return dcc.Graph(id='restaurant-map-graph', figure=fig)
    
def load_all_place_names():
    """Load all place names from restaurants, hotels, and attractions CSV files"""
    places = []
    
    try:
        # Load restaurants
        restaurants_df = pd.read_csv('data/restaurant.csv', encoding='utf-8-sig')
        for _, row in restaurants_df.iterrows():
            places.append({
                'id': row.get('Restaurant_ID'),
                'name': row.get('Name', ''),
                'type': 'Restaurant',
                'lat': row.get('Lat'),
                'lon': row.get('Long')
            })
    except Exception as e:
        print(f"Error loading restaurants: {e}")
    
    try:
        # Load hotels
        hotels_df = pd.read_csv('data/hotels.csv', encoding='utf-8-sig')
        for _, row in hotels_df.iterrows():
            places.append({
                'id': row.get('Hotel_ID'),
                'name': row.get('HotelName', ''),
                'type': 'Hotel',
                'lat': row.get('Lat'),
                'lon': row.get('Long')
            })
    except Exception as e:
        print(f"Error loading hotels: {e}")
    
    try:
        # Load attractions
        attractions_df = pd.read_csv('data/Kyoto_attractions.csv', encoding='utf-8-sig')
        for _, row in attractions_df.iterrows():
            places.append({
                'id': row.get('ID'),
                'name': row.get('Name', ''),
                'type': 'Attraction',
                'lat': row.get('Lat'),
                'lon': row.get('Lng', row.get('Long'))  # Try both column names
            })
    except Exception as e:
        print(f"Error loading attractions: {e}")
    
    # Filter out entries with missing coordinates or names
    places = [p for p in places if p['name'] and pd.notna(p['lat']) and pd.notna(p['lon'])]
    
    return places

def create_hotel_map_chart():
    """Creates a mapbox scatter plot of all hotels."""
    try:
        # [防呆] 嘗試讀取資料
        df = get_all_hotels()
        if df is None or df.empty:
            raise ValueError("No data returned from database")

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
                bgcolor='rgba(0, 53, 128, 0.5)',
                font=dict(color='white')
            ),
            clickmode='event+select',
            hoverdistance=20
        )
        fig.update_traces(
            hovertemplate='<b>%{hovertext}</b><br>' +
                          'Hotel: %{customdata[1]}<br>' +
                          '<i>Click to view details</i><extra></extra>',
            marker=dict(size=12, opacity=0.9),
            hoverlabel=dict(bgcolor='#003580', font_size=14, font_family='Arial, sans-serif')
        )
        return dcc.Graph(
            id='hotel-map-graph',
            figure=fig,
            config={'displayModeBar': True, 'scrollZoom': True, 'doubleClick': 'reset', 'modeBarButtonsToRemove': ['lasso2d', 'select2d']}
        )
    except Exception as e:
        print(f"⚠️ Warning: Could not load Hotel Map. Error: {e}")
        fig = go.Figure()
        fig.update_layout(title="Map Data Unavailable", xaxis={'visible': False}, yaxis={'visible': False})
        return dcc.Graph(id='hotel-map-graph', figure=fig)

def create_attraction_map_chart():
    """Creates a mapbox scatter plot of all attractions."""
    try:
        # [防呆] 嘗試讀取資料
        df = get_all_attractions()
        if df is None or df.empty:
            raise ValueError("No data returned from database")

        # Filter out entries without coordinates
        df = df.dropna(subset=['Lat', 'Long'])

        # Create 'RatingCategory' based on 'Rating'
        bins = [0, 2, 3, 4, 5]
        labels = ['1-2 Stars', '2-3 Stars', '3-4 Stars', '4-5 Stars']
        df['RatingCategory'] = pd.cut(df['Rating'], bins=bins, labels=labels, right=False, include_lowest=True)

        # Ensure ID is integer
        df['ID_int'] = df['ID'].astype(int)

        fig = px.scatter_map(
            df,
            lat="Lat",
            lon="Long",
            hover_name="Name",
            hover_data={"Rating": ':.1f', "Type": True, "RatingCategory": True},
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
            custom_data=['ID_int', 'Name']  # Add Attraction ID for click handling
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
                bgcolor='rgba(0, 53, 128, 0.5)',
                font=dict(color='white')
            ),
            clickmode='event+select',
            hoverdistance=20
        )
        fig.update_traces(
            hovertemplate='<b>%{hovertext}</b><br>' +
                          'Attraction: %{customdata[1]}<br>' +
                          '<i>Click to view details</i><extra></extra>',
            marker=dict(size=12, opacity=0.9),
            hoverlabel=dict(bgcolor='#003580', font_size=14, font_family='Arial, sans-serif')
        )
        return dcc.Graph(
            id='attraction-map-graph',
            figure=fig,
            config={'displayModeBar': True, 'scrollZoom': True, 'doubleClick': 'reset', 'modeBarButtonsToRemove': ['lasso2d', 'select2d']}
        )
    except Exception as e:
        print(f"⚠️ Warning: Could not load Attraction Map. Error: {e}")
        fig = go.Figure()
        fig.update_layout(title="Map Data Unavailable", xaxis={'visible': False}, yaxis={'visible': False})
        return dcc.Graph(id='attraction-map-graph', figure=fig)

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
                style={'backgroundColor': '#FFFFFF', 'border': '1px solid #E8ECEF', 'color': '#4A5568', 'marginBottom': '15px'}
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
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#E8ECEF'),
        margin=dict(l=40, r=20, t=60, b=40)
    )
    fig_revenue.update_traces(line_color='#003580', fillcolor='rgba(0, 53, 128, 0.2)')

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
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#E8ECEF'),
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # --- 4. 定義解釋文案 ---
    help_rev = [
        html.H5("營收趨勢解讀", style={'color': '#003580'}),
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
        html.H3('Analytics Dashboard', style={'color': '#003580', 'marginTop': '2rem', 'marginBottom': '1rem', 'borderBottom': '1px solid #E8ECEF', 'paddingBottom': '10px'}),
        
        html.Div([
            # 左圖：營收
            html.Div([
                create_help_section('rev-detail-help', 'About Revenue', help_rev),
                dcc.Graph(figure=fig_revenue, style={'height': '500px'})
            ], style={'flex': '1', 'minWidth': '400px', 'backgroundColor': '#F2F6FA', 'padding': '10px', 'borderRadius': '8px'}),
            
            # 右圖：狀態
            html.Div([
                create_help_section('status-detail-help', 'About Cancellations', help_status),
                dcc.Graph(figure=fig_status, style={'height': '500px'})
            ], style={'flex': '1', 'minWidth': '400px', 'backgroundColor': '#F2F6FA', 'padding': '10px', 'borderRadius': '8px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '2rem'})
    ])

# ==========================================
#  CP Analysis Functions (Visualizations)
# ==========================================

def create_interactive_map(df):
    """建立互動式地圖 (上方)"""
    fig = px.scatter_mapbox(
        df,
        lat="Lat", lon="Long",
        hover_name="Name",
        hover_data=["TotalRating", "AvgPrice"],
        color="TotalRating",
        color_continuous_scale="Bluered", # 紅色代表高分
        size_max=15,
        zoom=12,
        height=450
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0},
        clickmode='event+select', # 允許點擊和框選
        dragmode='pan' # 預設拖曳模式
    )
    return fig

def create_cp_matrix(df):
    """建立 CP 值矩陣圖 (下方)"""
    # 畫散佈圖
    fig = px.scatter(
        df,
        x="AvgPrice", 
        y="TotalRating",
        color="FirstCategory", # 用料理類型上色
        size="ReviewNum",      # 評論越多點越大
        hover_name="Name",
        height=400,
        labels={"AvgPrice": "Average Price (¥)", "TotalRating": "Rating (Stars)"},
        template="plotly_white"
    )
    
    # 加入 "高 CP 值" 區域標示 (左上角：低價高分)
    fig.add_shape(type="rect",
        x0=0, y0=4.0, x1=3000, y1=5.0,
        line=dict(color="Green", width=2, dash="dot"),
        fillcolor="rgba(0, 255, 0, 0.1)",
    )
    fig.add_annotation(x=1500, y=4.8, text="🔥 High CP Zone", showarrow=False, font=dict(color="green", size=14, weight="bold"))

    return fig

def create_advanced_analytics_layout():
    """建立進階分析頁面 Layout (含狀態記憶與景點資訊卡)"""
    
    # 1. 準備資料
    df_combined = get_combined_analytics_data()
    if df_combined.empty:
        import pandas as pd
        df_combined = pd.DataFrame(columns=['ID', 'Name', 'Lat', 'Long', 'Rating', 'Price', 'Type', 'SubCategory'])

    # 2. 建立景點下拉選單
    attractions_options = []
    if not df_combined.empty and 'Type' in df_combined.columns:
        att_df = df_combined[df_combined['Type'] == 'Attraction'].copy()
        att_df['Name'] = att_df['Name'].astype(str).str.strip()
        att_df = att_df.sort_values('Name')
        for _, row in att_df.iterrows():
            if row['Name'] and row['Name'].lower() != 'nan':
                attractions_options.append({'label': row['Name'], 'value': row['ID']})

    # 3. 建立 Layout
    return html.Div([

        # Header
        html.Div([
            html.Button([html.I(className='fas fa-arrow-left'), ' Back'], id={'type': 'back-btn', 'index': 'analytics'}, className='btn-secondary'),
            html.H1("Smart Travel Decision Board", style={'color': '#003580', 'marginLeft': '2rem'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '1.5rem', 'borderBottom': '1px solid #E8ECEF', 'paddingBottom':'1rem'}),

        # --- 控制面板區 ---
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Label([html.I(className="fas fa-search-location me-2"), "Focus on Attraction:"], style={'fontWeight':'bold', 'color': '#1A1A1A'}),
                    dcc.Dropdown(
                        id='analytics-attraction-search',
                        options=attractions_options,
                        placeholder="Search & Click an attraction to analyze nearby...",
                        style={'fontSize': '0.9rem', 'color': '#000'},
                        searchable=True, 
                        clearable=True,
                        # [NEW] 關鍵修改：啟用狀態記憶 (解決問題 2)
                        persistence=True,
                        persistence_type='session' # 即使重新整理或跳轉頁面，只要瀏覽器沒關，值都會在
                    )
                ], width=6),
                dbc.Col([
                    html.Label([html.I(className="fas fa-layer-group me-2"), "Show on Matrix:"], style={'fontWeight':'bold', 'color': '#1A1A1A'}),
                    dbc.Checklist(
                        options=[{"label": "Restaurants", "value": "Restaurant"}, {"label": "Hotels", "value": "Hotel"}],
                        value=["Restaurant", "Hotel"],
                        id="analytics-type-filter", inline=True, switch=True,
                        # [NEW] 這個也可以記憶
                        persistence=True, persistence_type='session'
                    )
                ], width=6, style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
            ], className="mb-3 p-3 bg-white rounded shadow-sm border")
        ]),

        # --- [NEW] 景點詳細資訊區 (解決問題 3) ---
        # 這個 Div 會由 Callback 自動填入內容
        html.Div(id='analytics-attraction-info', style={'marginBottom': '20px'}),

        # --- 上半部：互動式地圖 ---
        html.Div([
            dcc.Graph(
                id='interactive-map', 
                style={'height': '500px'},
                config={'displayModeBar': True, 'scrollZoom': True}
            )
        ], style={'marginBottom': '20px', 'boxShadow': '0 4px 12px rgba(0,0,0,0.1)', 'borderRadius': '8px', 'overflow': 'hidden'}),

        # --- 中半部：CP 矩陣 ---
        html.Div([
            html.Div([
                html.H4("Cost-Performance Matrix", style={'color': '#003580', 'display':'inline-block'}),
                html.Span(id='matrix-status-text', style={'marginLeft':'15px', 'color':'#666', 'fontSize':'0.9rem'})
            ], style={'padding': '20px 20px 0 20px'}),
            dcc.Graph(id='cp-matrix-graph', style={'height': '400px'})
        ], style={'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 12px rgba(0,0,0,0.1)', 'marginBottom': '30px'}),
        
        # --- 下半部：詳細資料列表 ---
        html.Div([
            html.H3("Selected Candidates", style={'color': '#003580', 'marginBottom': '15px'}),
            dbc.Tabs([
                dbc.Tab(label="High CP Restaurants", tab_id="tab-analytics-restaurants", label_style={"color": "#32CD32", "fontWeight": "bold"}),
                dbc.Tab(label="High CP Hotels", tab_id="tab-analytics-hotels", label_style={"color": "#FF4500", "fontWeight": "bold"}),
            ], id="analytics-tabs", active_tab="tab-analytics-restaurants"),
            
            html.Div(id="analytics-list-content", style={'padding': '20px', 'backgroundColor': 'white', 'minHeight': '200px', 'borderRadius': '0 0 8px 8px'})
        ], style={'marginBottom': '50px', 'marginTop': '50px'}),

        # Stores
        dcc.Store(id='analytics-combined-data', data=df_combined.to_dict('records')),

    ], style={'padding': '2rem', 'maxWidth': '1400px', 'margin': '0 auto', 'minHeight': '100vh'})

##########################
####   初始化應用程式   ####
##########################
app = Dash(__name__, external_stylesheets=[
    '/assets/bootstrap.min.css',
    '/assets/fontawesome-local.css',
    '/assets/voyage_styles.css'
],
           title='柔成員的旅遊平台',
           suppress_callback_exceptions=True)
server = app.server

# Suppress React defaultProps warnings in console
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script>
            // Suppress React warnings from Dash internal components
            const originalWarn = console.warn;
            const originalError = console.error;

            console.warn = function(...args) {
                if (args[0] && typeof args[0] === 'string') {
                    // Suppress defaultProps warnings
                    if (args[0].includes('defaultProps')) return;
                    // Suppress componentWillMount warnings
                    if (args[0].includes('componentWillMount')) return;
                    if (args[0].includes('UNSAFE_componentWillMount')) return;
                    // Suppress other React lifecycle warnings
                    if (args[0].includes('componentWillReceiveProps')) return;
                    if (args[0].includes('componentWillUpdate')) return;
                }
                originalWarn.apply(console, args);
            };

            console.error = function(...args) {
                if (args[0] && typeof args[0] === 'string') {
                    // Suppress React lifecycle errors
                    if (args[0].includes('componentWillMount')) return;
                    if (args[0].includes('defaultProps')) return;
                }
                originalError.apply(console, args);
            };
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ===== 版面配置 =====
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Store(id='current-user-data', storage_type='session'),
    dcc.Store(id='page-mode', data='login', storage_type='memory'),
    dcc.Store(id='current-page', data='overview', storage_type='memory'),
    dcc.Store(id='menu-open', data=False, storage_type='memory'),
    dcc.Store(id='view-mode', data='home', storage_type='memory'),
    dcc.Store(id='navigation-trigger', storage_type='memory'),
    dcc.Store(id='search-cuisine', storage_type='memory'),
    dcc.Store(id='search-rating', storage_type='memory'),
    dcc.Store(id='active-dropdown', storage_type='memory', data=None),
    dcc.Store(id='close-dropdowns-trigger', storage_type='memory'),
    dcc.Store(id='selected-restaurant-id', storage_type='memory'),
    dcc.Store(id='previous-page-location', storage_type='memory'),
    dcc.Store(id='from-map-navigation', storage_type='memory'),
    dcc.Store(id='restaurant-detail-data', storage_type='memory'),
    dcc.Store(id='search-results-store', storage_type='memory'),
    dcc.Store(id='current-page-store', data=1, storage_type='memory'),
    dcc.Store(id='search-params-store', storage_type='memory'),
    dcc.Store(id='search-hotel-type', storage_type='memory'),
    dcc.Store(id='hotel-search-results-store', storage_type='memory'),
    dcc.Store(id='hotel-current-page-store', data=1, storage_type='memory'),
    dcc.Store(id='hotel-detail-data', storage_type='memory'),
    dcc.Store(id='selected-restaurants', storage_type='session', data=[]),
    dcc.Store(id='attraction-search-results-store', storage_type='memory'),
    dcc.Store(id='attraction-current-page-store', data=1, storage_type='memory'),
    dcc.Store(id='attraction-search-params-store', storage_type='memory'),
    dcc.Store(id='selected-attraction-type', storage_type='memory'),
    dcc.Store(id='selected-attraction-rating', storage_type='memory'),
    dcc.Store(id='analytics-selected-attraction', storage_type='session'),
    dcc.Store(id='analytics-combined-data', storage_type='memory'),
    dcc.Store(id='is-analytics-active', data=False, storage_type='memory'),
    dcc.Store(id='dropdown-open', data=False, storage_type='memory'),
    dcc.Store(id='dropdown-open-list', data=False, storage_type='memory'),
    dcc.Store(id='dropdown-open-hotel-list', data=False, storage_type='memory'),
    dcc.Store(id='dropdown-open-detail', data=False, storage_type='memory'),
    dcc.Store(id='previous-view-mode', storage_type='memory'),
    dcc.Store(id='previous-pathname', storage_type='memory'),
    dcc.Store(id='traffic-map-store', storage_type='memory', data={'points': []}),
    # ADD THIS LINE - Load all place names for traffic calculator
    dcc.Store(id='all-places-store', data=load_all_place_names(), storage_type='memory'),
    html.Div(id='scroll-trigger', style={'display': 'none'}),
    html.Div(id='page-content', style={'minHeight': '100vh'})
], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})

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
                            html.Img(
                                id='user-avatar-img-profile',
                                src=None,
                                style={
                                    'width': '40px',
                                    'height': '40px',
                                    'borderRadius': '50%',
                                    'objectFit': 'cover',
                                    'display': 'none'
                                }
                            ),
                            html.I(
                                id='user-avatar-icon-profile',
                                className='fas fa-user',
                                style={'display': 'block'}
                            )
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
                    'color': '#003580',
                    'fontSize': '2.5rem',
                    'marginBottom': '2rem',
                    'textAlign': 'center'
                }),

                # Profile Card
                html.Div([
                    # User Avatar Icon with Upload
                    html.Div([
                        # Display current photo or default icon
                        html.Div([
                            html.Img(
                                id='profile-photo-display',
                                src=user_data.get('profile_photo') if user_data.get('profile_photo') else None,
                                style={
                                    'width': '150px',
                                    'height': '150px',
                                    'borderRadius': '50%',
                                    'objectFit': 'cover',
                                    'border': '3px solid #003580',
                                    'display': 'block' if user_data.get('profile_photo') else 'none'
                                }
                            ),
                            html.I(
                                className='fas fa-user-circle',
                                id='profile-default-icon',
                                style={
                                    'fontSize': '6rem',
                                    'color': '#003580',
                                    'display': 'none' if user_data.get('profile_photo') else 'block'
                                }
                            )
                        ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '1rem'}),

                        # Upload button
                        html.Div([
                            dcc.Upload(
                                id='upload-profile-photo',
                                children=html.Div([
                                    html.I(className='fas fa-camera', style={'marginRight': '0.5rem'}),
                                    'Upload Photo'
                                ]),
                                style={
                                    'width': '150px',
                                    'height': '40px',
                                    'lineHeight': '40px',
                                    'borderRadius': '20px',
                                    'textAlign': 'center',
                                    'backgroundColor': '#003580',
                                    'color': '#FFFFFF',
                                    'cursor': 'pointer',
                                    'fontWeight': '600',
                                    'transition': 'all 0.3s ease',
                                    'margin': '0 auto',
                                    'boxShadow': '0 2px 8px rgba(0, 53, 128, 0.2)',
                                    'border': 'none',
                                    'outline': 'none',
                                    'display': 'inline-block',
                                    'overflow': 'hidden'
                                },
                                multiple=False,
                                accept='image/*'
                            )
                        ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '1rem', 'border': 'none', 'outline': 'none'}),

                        # Upload feedback message
                        html.Div(id='upload-feedback', style={
                            'textAlign': 'center',
                            'color': '#003580',
                            'fontSize': '0.9rem',
                            'minHeight': '20px'
                        })
                    ], style={'textAlign': 'center', 'marginBottom': '2rem'}),

                    # User Information
                    html.Div([
                        # Username
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-user', style={'marginRight': '0.5rem', 'color': '#003580'}),
                                html.Span('Username:', style={'fontWeight': 'bold', 'color': '#003580'})
                            ], style={'marginBottom': '0.5rem'}),
                            html.Div(user_data.get('username', 'N/A'), style={'fontSize': '1.2rem', 'color': '#1A1A1A'})
                        ], style={'marginBottom': '1.5rem'}),

                        # Email
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-envelope', style={'marginRight': '0.5rem', 'color': '#003580'}),
                                html.Span('Email:', style={'fontWeight': 'bold', 'color': '#003580'})
                            ], style={'marginBottom': '0.5rem'}),
                            html.Div(user_data.get('email', 'Not provided'), style={'fontSize': '1.2rem', 'color': '#1A1A1A'})
                        ], style={'marginBottom': '1.5rem'}),

                        # Account Created
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-calendar-plus', style={'marginRight': '0.5rem', 'color': '#003580'}),
                                html.Span('Member Since:', style={'fontWeight': 'bold', 'color': '#003580'})
                            ], style={'marginBottom': '0.5rem'}),
                            html.Div(created_at, style={'fontSize': '1.2rem', 'color': '#1A1A1A'})
                        ], style={'marginBottom': '1.5rem'}),

                        # Last Login
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-clock', style={'marginRight': '0.5rem', 'color': '#003580'}),
                                html.Span('Last Login:', style={'fontWeight': 'bold', 'color': '#003580'})
                            ], style={'marginBottom': '0.5rem'}),
                            html.Div(last_login, style={'fontSize': '1.2rem', 'color': '#1A1A1A'})
                        ], style={'marginBottom': '1.5rem'}),
                    ], style={'padding': '2rem'})
                ], style={
                    'backgroundColor': '#FFFFFF',
                    'borderRadius': '12px',
                    'padding': '2rem',
                    'maxWidth': '600px',
                    'margin': '0 auto',
                    'boxShadow': '0 4px 12px rgba(0, 53, 128, 0.12)',
                    'border': '1px solid #E8ECEF'
                })
            ], style={
                'maxWidth': '1200px',
                'margin': '0 auto',
                'padding': '7rem 2rem 3rem 2rem'
            })
        ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})
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
                    html.Div('Analytics', className='nav-link', id='nav-analytics', n_clicks=0),
                    html.Div('Traffic', className='nav-link', id='nav-traffic', n_clicks=0)
                ], className='header-nav'),

                # Actions
                html.Div([
                    create_primary_button('Create a Trip', button_id='create-trip-btn', icon='fas fa-plus'),

                    # User Avatar with Dropdown
                    html.Div([
                        html.Div([
                            html.Img(
                                id='user-avatar-img',
                                src=None,
                                style={
                                    'width': '40px',
                                    'height': '40px',
                                    'borderRadius': '50%',
                                    'objectFit': 'cover',
                                    'display': 'none'
                                }
                            ),
                            html.I(
                                id='user-avatar-icon',
                                className='fas fa-user',
                                style={'display': 'block'}
                            )
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

        # ===== Attractions Section (新增) =====
        html.Div([
            html.Div([
                html.H2('Must-Visit Attractions', className='section-title'),
                html.A(['View All', html.I(className='fas fa-arrow-right')], 
                       className='view-all-link', id='view-all-attractions', n_clicks=0)
            ], className='section-header'),
            html.Div([
                html.Div(id='attractions-card-container', className='card-row')
            ], className='card-scroll-container')
        ], className='content-section'),
        
        # ===== Personalized Content Section (Favorites) =====
        html.Div([
            html.H2('My Favorites Collection', className='section-title'),

            # Tab Navigation for Favorites
            html.Div([
                html.Div('Restaurants', id='fav-tab-rest', className='tab-item active', n_clicks=0),
                html.Div('Hotels', id='fav-tab-hotel', className='tab-item', n_clicks=0),
                html.Div('Attractions', id='fav-tab-attr', className='tab-item', n_clicks=0)
            ], className='tab-navigation'),

            # Favorites Content Container (由 Callback 填充)
            html.Div(id='favorites-content-container', style={'minHeight': '200px', 'padding': '1rem 0'})
        ], className='content-section'),

        # ===== NEW: Map Section =====
        html.Div([
            html.H2('Distribution in Kyoto', className='section-title', id='distribution-map-section'),
            html.Div([
                dcc.RadioItems(
                    id='map-type-switch',
                    options=[
                        {'label': 'Restaurants', 'value': 'restaurants'},
                        {'label': 'Hotels', 'value': 'hotels'},
                        {'label': 'Attractions', 'value': 'attractions'},
                    ],
                    value='restaurants',
                    className='map-toggle-buttons',
                    labelClassName='map-toggle-label',
                    inputClassName='map-toggle-input'
                )
            ], className='map-toggle-container'),
            html.Div(id='map-container', children=[create_restaurant_map_chart()])
        ], className='content-section')
    ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})

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
                    ], id={'type': 'back-btn', 'index': 'restaurant-list'}, className='btn-back', n_clicks=0),
                    html.H1('Restaurant Directory', style={
                        'color': '#003580',
                        'marginLeft': '2rem',
                        'fontSize': '2rem',
                        'fontWeight': 'bold'
                    })
                ], style={'display': 'flex', 'alignItems': 'center'}),

                # User Avatar
                html.Div([
                    html.Div([
                        html.Img(
                            id='user-avatar-img-list',
                            src=None,
                            style={
                                'width': '40px',
                                'height': '40px',
                                'borderRadius': '50%',
                                'objectFit': 'cover',
                                'display': 'none'
                            }
                        ),
                        html.I(
                            id='user-avatar-icon-list',
                            className='fas fa-user',
                            style={'display': 'block'}
                        )
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
            'backgroundColor': '#F2F6FA',
            'borderBottom': '1px solid #E8ECEF',
            'position': 'sticky',
            'top': '0',
            'zIndex': '1000'
        }),

        # ===== Search and Filter Section =====
        html.Div([
            html.Div([
                # Search bar
                create_compound_search_bar(),

                # Search stats
                html.Div(id='search-stats', style={
                    'color': '#555555',
                    'fontSize': '0.95rem',
                    'marginTop': '1rem',
                    'fontWeight': '500'
                })
            ], style={
                'maxWidth': '1000px',
                'margin': '0 auto'
            })
        ], style={
            'backgroundColor': '#F2F6FA',
            'padding': '2rem',
            'borderBottom': '1px solid #222'
        }),

        # ===== Restaurant Grid =====
        html.Div([
            html.Div(id='restaurant-grid', className='restaurant-list-grid')
        ], style={
            'backgroundColor': '#F2F6FA',
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
            'backgroundColor': '#F2F6FA'
        }),

    ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})

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
                    ], id={'type': 'back-btn', 'index': 'hotel-list'}, className='btn-back', n_clicks=0),
                    html.H1('Hotel Directory', style={
                        'color': '#003580',
                        'marginLeft': '2rem',
                        'fontSize': '2rem',
                        'fontWeight': 'bold'
                    })
                ], style={'display': 'flex', 'alignItems': 'center'}),

                # User Avatar
                html.Div([
                    html.Div([
                        html.Img(
                            id='user-avatar-img-hotel-list',
                            src=None,
                            style={
                                'width': '40px',
                                'height': '40px',
                                'borderRadius': '50%',
                                'objectFit': 'cover',
                                'display': 'none'
                            }
                        ),
                        html.I(
                            id='user-avatar-icon-hotel-list',
                            className='fas fa-user',
                            style={'display': 'block'}
                        )
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
            'backgroundColor': '#F2F6FA',
            'borderBottom': '1px solid #E8ECEF',
            'position': 'sticky',
            'top': '0',
            'zIndex': '1000'
        }),

        # ===== Search and Filter Section =====
        html.Div([
            html.Div([
                # Search bar
                create_hotel_search_bar(),

                # Search stats
                html.Div(id='hotel-search-stats', style={
                    'color': '#555555',
                    'fontSize': '0.95rem',
                    'marginTop': '1rem',
                    'fontWeight': '500'
                })
            ], style={
                'maxWidth': '1000px',
                'margin': '0 auto'
            })
        ], style={
            'backgroundColor': '#F2F6FA',
            'padding': '2rem',
            'borderBottom': '1px solid #222'
        }),

        # ===== Hotel Grid =====
        html.Div([
            html.Div(id='hotel-grid', className='restaurant-list-grid')
        ], style={
            'backgroundColor': '#F2F6FA',
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
            'backgroundColor': '#F2F6FA'
        })
    ], style={'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})

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
            n_clicks=0
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
                n_clicks=0
            )
        )
        if start_page > 2:
            buttons.append(html.Span('...', style={'color': '#4A5568', 'padding': '0 0.5rem'}))

    # Middle pages
    for page in range(start_page, end_page + 1):
        is_active = page == current_page
        buttons.append(
            html.Button(
                str(page),
                id={'type': 'page-btn', 'index': page},
                className='pagination-btn active' if is_active else 'pagination-btn',
                n_clicks=0
            )
        )

    # Last page
    if end_page < total_pages:
        if end_page < total_pages - 1:
            buttons.append(html.Span('...', style={'color': '#4A5568', 'padding': '0 0.5rem'}))
        buttons.append(
            html.Button(
                str(total_pages),
                id={'type': 'page-btn', 'index': total_pages},
                className='pagination-btn',
                n_clicks=0
            )
        )

    # Next button
    buttons.append(
        html.Button(
            [html.I(className='fas fa-chevron-right')],
            id={'type': 'page-btn', 'index': 'next'},
            disabled=current_page == total_pages,
            className='pagination-btn',
            n_clicks=0
        )
    )

    return buttons


TRAFFIC_GUIDE_EN = """
# Navigating Kyoto: A Guide to Public Transportation

Kyoto has an excellent public transport system. For most travelers, the most efficient way to get around is by using a combination of the city's subways, buses, and trains.

## 1. The Kyoto Bus System

- **How it Works:** The city is primarily served by the green Kyoto City Buses and the red-and-cream Kyoto Buses. Most of central Kyoto is a "flat-fare zone."
- **How to Ride:** Board from the rear door, and exit from the front door, next to the driver.
- **Payment:** The flat fare is typically ¥230. You can pay with cash (exact change is appreciated) or by tapping a major IC card (like Suica, Pasmo, or ICOCA) on the reader as you exit.

## 2. The Kyoto Subway System

- **The Lines:** There are two simple-to-use subway lines:
    - **Karasuma Line:** Runs north-south.
    - **Tozai Line:** Runs east-west.
- **Why Use It:** Subways are the fastest way to travel longer distances across the city, bypassing all traffic. They are great for reaching major hubs like Kyoto Station.

## 3. Popular Travel Passes

- **Bus & Subway 1-Day Pass:**
    - **Price:** Adults ¥1100, Children ¥550.
    - **Coverage:** Unlimited rides on all Kyoto City Buses, Kyoto Buses, and both subway lines for one calendar day. A great all-in-one option.
- **Subway 1-Day Pass:**
    - **Price:** Adults ¥800, Children ¥400.
    - **Coverage:** Unlimited rides on both the Karasuma and Tozai subway lines. Best if you plan to cover long distances quickly.

## 4. Route Map

For a detailed, zoomable map of the entire bus and subway network, it is highly recommended to download the official PDF guide.

[**Download Official Kyoto Bus & Subway Route Map (PDF)**](https://www2.city.kyoto.lg.jp/kotsu/webguide/files/tikabusnavi/en_tikabusnavi_2.pdf)

This map is invaluable for planning your routes and seeing how different lines connect.
"""

TRAFFIC_GUIDE_ZH = """
# 京都導航：公共交通指南

京都有一個優秀的公共交通系統。對於大多數遊客來說，最有效的出行方式是結合使用市內的地下鐵、巴士和火車。

## 1. 京都巴士系統

- **如何運作：** 該市主要由綠色的京都市營巴士和紅白相間的京都巴士提供服務。京都市中心大部分地區為「單一票價區」。
- **如何乘車：** 從後門上車，從司機旁邊的前門下車。
- **付款方式：** 單一票價通常為230日元。您可以使用現金（請準備好零錢）或在下車時在讀卡器上輕觸主要的IC卡（如Suica、Pasmo或ICOCA）支付。

## 2. 京都地下鐵系統

- **線路：** 有兩條簡單易用的地下鐵線路：
    - **烏丸線：** 南北運行。
    - **東西線：** 東西運行。
- **為何使用：** 地下鐵是穿越城市長距離最快的方式，可避開所有交通擁堵。非常適合到達京都站等主要樞紐。

## 3. 熱門交通票券

- **巴士與地下鐵一日通票：**
    - **價格：** 成人1100日元，兒童550日元。
    - **覆蓋範圍：** 在一個日曆日內無限次乘坐所有京都市營巴士、京都巴士以及兩條地下鐵線路。是一個極佳的一體化選擇。
- **地下鐵一日通票：**
    - **價格：** 成人800日元，兒童400日元。
    - **覆蓋範圍：** 無限次乘坐烏丸線和東西線兩條地下鐵線路。如果您計劃快速覆蓋長距離，這是最佳選擇。

## 4. 路線圖

為了獲得整個巴士和地下鐵網絡的詳細、可縮放的地圖，強烈建議下載官方的PDF指南。

[**下載官方京都巴士和地下鐵路線圖（PDF）**](https://www2.city.kyoto.lg.jp/kotsu/webguide/files/tikabusnavi/ja_tikabusnavi_2.pdf)

這張地圖對於規劃您的路線和了解不同線路的連接方式非常有價值。
"""


# ====== 認證相關 Callbacks ======

# 頁面路由控制
# 頁面路由控制 (修正版：優先權調整)
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
    clean_expired_sessions()
    
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # 檢查 session
    if session_data and 'session_id' in session_data:
        user_id = get_session(session_data['session_id'])
        if user_id:
            # === [關鍵修正] 優先檢查 URL pathname (詳細頁面優先) ===

            # 0. 檢查是否為 Create Trip 頁面
            if pathname == '/create-trip':
                return create_trip_layout(), 'main'

            # 1. 檢查是否為旅館詳細頁面
            if pathname and pathname.startswith('/hotel/'):
                try:
                    hotel_id = int(pathname.split('/')[-1])
                    return create_hotel_detail_page(hotel_id), 'main'
                except:
                    return create_main_layout(), 'main'

            # 2. 檢查是否為餐廳詳細頁面
            elif pathname and pathname.startswith('/restaurant/'):
                if restaurant_id_data and restaurant_id_data.get('id'):
                    return create_restaurant_detail_page(restaurant_id_data['id']), 'main'
                else:
                    # 如果直接輸入網址但沒有 ID store，嘗試從網址解析
                    try:
                         r_id = int(pathname.split('/')[-1])
                         return create_restaurant_detail_page(r_id), 'main'
                    except:
                         return create_restaurant_list_page(), 'main'
            
            # 3. 檢查景點詳細頁面
            elif pathname and pathname.startswith('/attraction/') and 'list' not in pathname:
                try:
                    # 解析 ID
                    url_parts = [p for p in pathname.split('/') if p]
                    if url_parts and url_parts[-1].isdigit():
                        a_id = int(url_parts[-1])
                        # 直接呼叫新的頁面生成器 (它會自己抓資料)
                        return create_attraction_detail_page(a_id), 'main'
                except Exception as e:
                    print(f"Error in display_page for attraction: {e}")
                    return create_main_layout(), 'main'

            # === 然後才檢查 view_mode (列表頁與功能頁) ===

            elif view_mode == 'profile':
                user_data = get_user_full_details(user_id)
                return create_profile_page(user_data), 'main'

            elif view_mode == 'hotel-list':
                return create_hotel_list_page(), 'main'

            # 檢查分析頁面
            elif view_mode == 'analytics':
                return create_advanced_analytics_layout(), 'main'
            
            # Find this section in the traffic layout (around line 1587)
            # Find this section in the traffic layout (around line 1587)
            elif view_mode == 'traffic':
                traffic_layout = html.Div([
                    # Header
                    html.Div([
                        html.Button([html.I(className='fas fa-arrow-left'), ' Back'], 
                                id={'type': 'back-btn', 'index': 'traffic'}, 
                                className='btn-secondary'),
                        html.H1("Kyoto Transportation Guide", 
                            style={'color': '#003580', 'marginLeft': '2rem'})
                    ], style={'display': 'flex', 'alignItems': 'center', 'padding': '2rem', 
                            'borderBottom': '1px solid #E8ECEF'}),
                    
                    # Toggle buttons
                    html.Div([
                        html.Div([
                            dbc.Button([
                                html.I(className='fas fa-search-location', style={'marginRight': '8px'}),
                                'Text Search Calculator'
                            ], id='toggle-text-calculator', color='primary', size='lg',
                            style={'marginRight': '1rem', 'minWidth': '250px'}),
                            
                            dbc.Button([
                                html.I(className='fas fa-map-marked-alt', style={'marginRight': '8px'}),
                                'Map Click Calculator'
                            ], id='toggle-map-calculator', color='secondary', size='lg',
                            style={'minWidth': '250px'})
                        ], style={
                            'display': 'flex',
                            'justifyContent': 'center',
                            'padding': '2rem 0'
                        })
                    ]),
                    
                    # Store to track which calculator is active
                    dcc.Store(id='active-calculator', data='text'),
                    
                    # Text-based calculator (visible by default)
                    html.Div([
                        html.Div([
                            html.H2("Distance Calculator", 
                                style={'color': '#003580', 'marginBottom': '1rem', 'textAlign': 'center'}),
                            html.P("Calculate distance between any two places in Kyoto", 
                                style={'color': '#666', 'marginBottom': '2rem', 'textAlign': 'center'}),
                            
                            # First location input
                            html.Div([
                                html.Label([
                                    html.I(className='fas fa-map-marker-alt', 
                                        style={'marginRight': '8px', 'color': '#32CD32'}),
                                    'Starting Point'
                                ], style={'fontWeight': 'bold', 'color': '#1A1A1A', 'marginBottom': '0.5rem'}),
                                # Find these lines in create traffic_layout (around line 1665-1680):
                                dcc.Dropdown(
                                    id='traffic-start-location',
                                    placeholder='Type to search (restaurants, hotels, attractions)...',
                                    searchable=True,
                                    clearable=True,
                                    style={
                                        'marginBottom': '1.5rem',
                                        'color': '#1A1A1A'  # Black text
                                    },
                                    # Add these new properties:
                                    optionHeight=50,
                                    maxHeight=300,
                                    # Add inline CSS for dropdown menu
                                    className='custom-location-dropdown'
                                )
                            ]),
                            
                            # Second location input
                            html.Div([
                                html.Label([
                                    html.I(className='fas fa-map-marker-alt', 
                                        style={'marginRight': '8px', 'color': '#FF4500'}),
                                    'Destination'
                                ], style={'fontWeight': 'bold', 'color': '#1A1A1A', 'marginBottom': '0.5rem'}),
                                dcc.Dropdown(
                                    id='traffic-end-location',
                                    placeholder='Type to search (restaurants, hotels, attractions)...',
                                    searchable=True,
                                    clearable=True,
                                    className='custom-location-dropdown',
                                    style={
                                        'marginBottom': '1.5rem',
                                        'color': '#1A1A1A'
                                        }
                                )
                            ]),
                            
                            # Calculate button
                            html.Div([
                                dbc.Button([
                                    html.I(className='fas fa-route', style={'marginRight': '8px'}),
                                    'Calculate Distance'
                                ], id='calculate-text-distance-btn', color='primary', size='lg',
                                style={'width': '100%', 'padding': '12px'})
                            ], style={'marginBottom': '2rem'}),
                            
                            # Text calculation result
                            html.Div(id='text-distance-result', style={
                                'padding': '1.5rem',
                                'backgroundColor': '#F2F6FA',
                                'borderRadius': '8px',
                                'border': '2px solid #E8ECEF',
                                'minHeight': '150px'
                            })
                        ], style={
                            'maxWidth': '800px',
                            'margin': '0 auto',
                            'padding': '2rem',
                            'backgroundColor': '#FFFFFF',
                            'borderRadius': '12px',
                            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
                        })
                    ], id='text-calculator-section', style={'padding': '2rem'}),
                    
                    # Map-based calculator (hidden by default)
                    html.Div([
                        html.Div([
                            html.H2("Map-Based Calculator", 
                                style={'color': '#003580', 'textAlign': 'center', 'marginBottom': '1rem'}),
                            html.P("Click on two points on the map to calculate distance", 
                                style={'textAlign': 'center', 'color': '#666', 'marginBottom': '1rem'}),
                            
                            html.Div([
                                html.Div([
                                    html.I(className='fas fa-map-marker-alt', 
                                        style={'marginRight': '10px', 'fontSize': '1.5rem', 'color': '#003580'}),
                                    html.Span("Click on markers to select points", 
                                            style={'fontSize': '1rem', 'fontWeight': '600', 'color': '#003580'})
                                ], style={'display': 'flex', 'alignItems': 'center', 
                                        'justifyContent': 'center', 'marginBottom': '10px'})
                            ], id='point-selection-instruction', style={
                                'backgroundColor': '#E6F3FF',
                                'padding': '1rem',
                                'borderRadius': '8px',
                                'border': '2px solid #003580',
                                'marginBottom': '1rem'
                            }),
                            
                            create_traffic_map_chart(),
                            
                            html.Div(id='distance-calculation-result', style={
                                'padding': '1.5rem',
                                'minHeight': '80px',
                                'backgroundColor': '#FFFFFF',
                                'borderRadius': '8px',
                                'border': '2px solid #E8ECEF',
                                'marginTop': '1rem',
                                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
                            })
                        ], style={
                            'maxWidth': '1200px',
                            'margin': '0 auto',
                            'padding': '2rem',
                            'backgroundColor': '#FFFFFF',
                            'borderRadius': '12px',
                            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
                        })
                    ], id='map-calculator-section', style={'display': 'none', 'padding': '2rem'})
                    
                ], style={
                    'backgroundColor': '#F2F6FA',
                    'minHeight': '100vh'
                })
                return traffic_layout, 'main'

            # 檢查餐廳列表頁面
            elif view_mode == 'restaurant-list':
                return create_restaurant_list_page(), 'main'
            
            elif view_mode == 'attraction-list':
                return create_attraction_list_page(), 'main'

            elif view_mode == 'analytics':
                return create_analytics_layout(analytics_df), 'main'

            # 預設顯示首頁
            else:
                return create_main_layout(), 'main'
            

    # 未登入
    if current_mode == 'register':
        return create_register_layout(), 'register'

    return create_login_layout(), 'login'

# Load user data (including profile photo) on page load/refresh
@app.callback(
    Output('current-user-data', 'data', allow_duplicate=True),
    [Input('session-store', 'data')],
    prevent_initial_call='initial_duplicate'
)
def load_user_data_on_refresh(session_data):
    """Load user data including profile photo from database on page load/refresh"""
    if not session_data or 'session_id' not in session_data:
        raise PreventUpdate

    # Validate session and get user ID
    user_id = get_session(session_data['session_id'])
    if not user_id:
        raise PreventUpdate

    # Get full user details from database
    user_details = get_user_full_details(user_id)
    if not user_details:
        raise PreventUpdate

    # Return user data including profile photo
    return {
        'user_id': user_id,
        'username': user_details.get('username'),
        'profile_photo': user_details.get('profile_photo')
    }


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
     Output('login-error-message', 'children'),
     Output('current-user-data', 'data')],
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

    # 額外檢查：確保觸發來源有實際的值（不是初始化的 None）
    # 這防止在頁面初次載入時顯示錯誤訊息
    if trigger_id == 'login-button' and not n_clicks:
        raise PreventUpdate
    if trigger_id == 'login-username' and not username_n_submit:
        raise PreventUpdate
    if trigger_id == 'login-password' and not password_n_submit:
        raise PreventUpdate

    # 移除使用者輸入的前後空白，再驗證（避免使用者多打空格造成比對失敗）
    if isinstance (username, str):
        username = username.strip()
    if isinstance(password, str):
        password = password.strip()
    # 驗證輸入
    if not username or not password:
        return no_update, dbc.Alert('請輸入使用者名稱和密碼', color='danger'), no_update

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

        # Get full user details including profile photo
        user_details = get_user_full_details(user_id)
        user_data = {
            'user_id': user_id,
            'username': user[1],
            'profile_photo': user_details.get('profile_photo') if user_details else None
        }

        return {'session_id': session_id, 'user_id': user_id, 'username': user[1]}, None, user_data
    else:
        return no_update, dbc.Alert('使用者名稱或密碼錯誤', color='danger'), no_update

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
    [Input('search-hotel', 'value'),
     Input('search-hotel-type', 'data')],
    prevent_initial_call=True
)
def handle_hotel_search(keyword, hotel_type):
    """處理旅館搜尋（主頁預覽，自動搜尋）"""
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
            html.I(className='fas fa-hotel', style={'fontSize': '3rem', 'color': '#003580', 'marginBottom': '1rem'}),
            html.H3('No hotels found', style={'color': '#1A1A1A'}),
            html.P('Try adjusting your search criteria', style={'color': '#888888'})
        ], style={'textAlign': 'center', 'padding': '4rem', 'width': '100%'})]
    
# Populate Attractions Cards on Homepage
@app.callback(
    Output('attractions-card-container', 'children'),
    [Input('url', 'pathname')]
)
def populate_attractions_cards(pathname):
    """填充景點卡片（橫向滾動）"""
    top_attractions = get_random_top_attractions(4, min_rating=4.0)

    if len(top_attractions) > 0:
        cards = [create_attraction_card(row) for _, row in top_attractions.iterrows()]
        return cards
    else:
        return [html.Div("No attractions found", style={'color': '#888', 'padding': '2rem'})]

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

# Navigate to attractions list page
@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('view-all-attractions', 'n_clicks')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def view_all_attractions(n_clicks, current_view):
    if n_clicks and current_view != 'attraction-list':
        return 'attraction-list'
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

@app.callback(
    Output('view-mode', 'data', allow_duplicate=True),
    [Input('nav-traffic', 'n_clicks')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def view_traffic(n_clicks, current_view):
    if n_clicks and current_view != 'traffic':
        return 'traffic'
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
    [Output('advanced-filters-panel', 'style'),
     Output('filter-icon', 'style')],
    [Input('toggle-advanced-filters', 'n_clicks')],
    [State('advanced-filters-panel', 'style')],
    prevent_initial_call=True
)
def toggle_advanced_filters(n_clicks, current_style):
    """切換進階篩選面板並旋轉圖標"""
    if n_clicks:
        if current_style and current_style.get('display') == 'block':
            # Close panel - rotate icon back to 0 degrees
            return {'display': 'none'}, {'marginRight': '8px', 'transform': 'rotate(0deg)', 'transition': 'transform 0.3s ease'}
        else:
            # Open panel - rotate icon to 180 degrees
            return {'display': 'block'}, {'marginRight': '8px', 'transform': 'rotate(180deg)', 'transition': 'transform 0.3s ease'}
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
        {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#1A1A1A'},
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
        {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#1A1A1A'},
        {'display': 'none'},
        None  # 重置 active-dropdown
    )

# Active filter chips removed - users can see filters in the filter panel

# Navigate to restaurant list when searching from homepage
# COMMENTED OUT: search-btn only exists on homepage, causes errors on other pages
# @app.callback(
#     Output('view-mode', 'data', allow_duplicate=True),
#     [Input('search-btn', 'n_clicks'),
#      Input('search-cuisine', 'data'),
#      Input('search-rating', 'data')],
#     [State('view-mode', 'data')],
#     prevent_initial_call=True
# )
# def navigate_to_search_results(n_clicks, cuisine, rating, current_view_mode):
#     """Navigate to restaurant list page when searching from homepage"""
#     # Only navigate if currently on homepage
#     if current_view_mode == 'home':
#         return 'restaurant-list'
#     raise PreventUpdate

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
            {'cursor': 'pointer', 'marginLeft': '10px', 'color': '#1A1A1A'},
            {'display': 'none'}, None)

# ====== Restaurant List Page Callbacks ======

# Handle search in restaurant list page with advanced filters
# 自动搜索：当选择料理类型、评分或价格范围或输入关键字时自动触发搜索
# Removed search-btn input to avoid errors when component doesn't exist on other pages
@app.callback(
    [Output('search-results-store', 'data'),
     Output('current-page-store', 'data', allow_duplicate=True),
     Output('search-params-store', 'data')],
    [Input('search-destination', 'value'),
     Input('search-cuisine', 'data'),
     Input('search-rating', 'data'),
     Input('price-range-filter', 'value')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def handle_restaurant_list_search(destination, cuisine, rating, price_range, view_mode):
    """處理餐廳列表頁的搜尋，並將結果存儲到 dcc.Store"""
    # 只有在列表頁面模式才觸發
    if view_mode != 'restaurant-list':
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
                      style={'fontSize': '4rem', 'color': '#003580', 'marginBottom': '2rem'}),
                html.H3('No restaurants found', style={'color': '#1A1A1A', 'marginBottom': '1rem'}),
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
                    'color': '#1A1A1A',
                    'fontSize': '1.2rem',
                    'fontWeight': 'bold',
                    'marginBottom': '0.3rem'
                }),
                html.Div(restaurant.get('JapaneseName', ''), style={
                    'color': '#666666',
                    'fontSize': '0.9rem',
                    'fontWeight': '400',
                    'marginBottom': '0.5rem'
                }),
                html.Div(f"{restaurant.get('FirstCategory', 'Restaurant')} - {restaurant.get('SecondCategory', '')}",
                        style={'color': '#003580', 'fontSize': '0.9rem', 'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span([
                        html.I(className='fas fa-star', style={'color': '#003580', 'marginRight': '5px'}),
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
            'backgroundColor': '#F2F6FA',
            'borderRadius': '8px',
            'overflow': 'hidden',
            'border': '1.5px solid #D0D5DD',
            'transition': 'transform 0.2s, border-color 0.2s',
            'cursor': 'pointer',
            'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
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

# Handle pagination button clicks - Universal for all page types
@app.callback(
    [Output('current-page-store', 'data', allow_duplicate=True),
     Output('hotel-current-page-store', 'data', allow_duplicate=True),
     Output('attraction-current-page-store', 'data', allow_duplicate=True)],
    [Input({'type': 'page-btn', 'index': ALL}, 'n_clicks')],
    [State('view-mode', 'data'),
     State('current-page-store', 'data'),
     State('hotel-current-page-store', 'data'),
     State('attraction-current-page-store', 'data'),
     State('search-results-store', 'data'),
     State('hotel-search-results-store', 'data'),
     State('attraction-search-results-store', 'data')],
    prevent_initial_call=True
)
def handle_pagination_click(n_clicks_list, view_mode, restaurant_page, hotel_page, attraction_page,
                           restaurant_results, hotel_results, attraction_results):
    """處理分頁按鈕點擊（通用於餐廳、旅館、景點列表頁）"""
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    # Get which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    import json as _json
    button_data = _json.loads(button_id)
    page_index = button_data['index']

    # Determine which page type we're on
    items_per_page = 15

    if view_mode == 'restaurant-list':
        current_page = restaurant_page
        search_results = restaurant_results
    elif view_mode == 'hotel-list':
        current_page = hotel_page
        search_results = hotel_results
    elif view_mode == 'attraction-list':
        current_page = attraction_page
        search_results = attraction_results
    else:
        raise PreventUpdate

    # Calculate total pages
    total_items = len(search_results) if search_results else 0
    total_pages = (total_items + items_per_page - 1) // items_per_page

    # Handle different button types
    if page_index == 'prev':
        new_page = max(1, current_page - 1)
    elif page_index == 'next':
        new_page = min(total_pages, current_page + 1)
    else:
        new_page = page_index

    # Return appropriate values based on view mode
    if view_mode == 'restaurant-list':
        return new_page, hotel_page, attraction_page
    elif view_mode == 'hotel-list':
        return restaurant_page, new_page, attraction_page
    elif view_mode == 'attraction-list':
        return restaurant_page, hotel_page, new_page
    else:
        raise PreventUpdate

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

# ====== Attraction List Page Callbacks (NEW) ======

# Update attraction list page avatar
@app.callback(
    [Output('user-avatar-img-attraction-list', 'src'),
     Output('user-avatar-img-attraction-list', 'style'),
     Output('user-avatar-icon-attraction-list', 'style')],
    [Input('current-user-data', 'data'),
     Input('view-mode', 'data')]
)
def update_attraction_list_avatar(user_data, view_mode):
    """更新景點列表頁使用者頭像"""
    if view_mode != 'attraction-list':
        raise PreventUpdate

    if not user_data:
        profile_photo = None
    else:
        profile_photo = user_data.get('profile_photo')

    if profile_photo:
        img_style = {'width': '40px', 'height': '40px', 'borderRadius': '50%', 'objectFit': 'cover', 'display': 'block'}
        icon_style = {'display': 'none'}
        return profile_photo, img_style, icon_style
    else:
        img_style = {'width': '40px', 'height': '40px', 'borderRadius': '50%', 'objectFit': 'cover', 'display': 'none'}
        icon_style = {'display': 'block'}
        return None, img_style, icon_style

# Toggle user dropdown in attraction list page
@app.callback(
    [Output('user-dropdown-attraction-list', 'className'),
     Output('dropdown-open', 'data', allow_duplicate=True)], # Using generic dropdown-open for simplicity or create specific
    [Input('user-avatar-attraction-list', 'n_clicks')],
    [State('dropdown-open', 'data')],
    prevent_initial_call=True
)
def toggle_user_dropdown_attraction_list(n_clicks, is_open):
    """切換景點列表頁的使用者下拉選單"""
    if n_clicks:
        new_state = not is_open
        className = 'user-dropdown show' if new_state else 'user-dropdown'
        return className, new_state
    raise PreventUpdate

# Navigate to profile from attraction list
@app.callback(
    [Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-view-mode', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('dropdown-profile-attraction-list', 'n_clicks')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def navigate_to_profile_from_attraction_list(n_clicks, current_view_mode):
    if n_clicks:
        return 'profile', current_view_mode or 'attraction-list', '/'
    raise PreventUpdate

# Handle logout from attraction list page dropdown
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout-attraction-list', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_dropdown_attraction_list(n_clicks, session_data):
    if not n_clicks:
        raise PreventUpdate
    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])
    return None

# ====== Profile Page Callbacks ======

# Navigate to profile page from home dropdown
@app.callback(
    [Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-view-mode', 'data', allow_duplicate=True)],
    [Input('dropdown-profile', 'n_clicks')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def navigate_to_profile_from_home(n_clicks, current_view_mode):
    """從首頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        # Store current view mode
        return 'profile', current_view_mode or 'home'
    raise PreventUpdate

# Navigate to profile page from restaurant list dropdown
@app.callback(
    [Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-view-mode', 'data', allow_duplicate=True),
     Output('selected-restaurant-id', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('dropdown-profile-list', 'n_clicks')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def navigate_to_profile_from_restaurant_list(n_clicks, current_view_mode):
    """從餐廳列表頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        # Store current view mode and clear restaurant ID to prevent detail page from showing
        return 'profile', current_view_mode or 'restaurant-list', {'id': None}, '/'
    raise PreventUpdate

# Navigate to profile page from hotel list dropdown
@app.callback(
    [Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-view-mode', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('dropdown-profile-hotel-list', 'n_clicks')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def navigate_to_profile_from_hotel_list(n_clicks, current_view_mode):
    """從旅館列表頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        # Store current view mode and change URL to prevent detail page from showing
        return 'profile', current_view_mode or 'hotel-list', '/'
    raise PreventUpdate

# Back button from profile page
@app.callback(
    [Output('view-mode', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('back-from-profile', 'n_clicks')],
    [State('previous-view-mode', 'data'),
     State('selected-restaurant-id', 'data'),
     State('previous-pathname', 'data')],
    prevent_initial_call=True
)
def back_from_profile(n_clicks, previous_view_mode, restaurant_id_data, previous_pathname):
    """從個人檔案頁返回上一頁"""
    if n_clicks:
        # If we came from a restaurant detail page, restore the restaurant URL
        if previous_view_mode == 'restaurant-detail' and restaurant_id_data and restaurant_id_data.get('id'):
            restaurant_id = restaurant_id_data['id']
            return 'home', f'/restaurant/{restaurant_id}'
        # If we came from a hotel detail page, restore the hotel URL
        elif previous_view_mode == 'hotel-detail' and previous_pathname:
            return 'home', previous_pathname
        # If we came from an attraction detail page, restore the attraction URL
        elif previous_view_mode == 'attraction-detail' and previous_pathname:
            return 'home', previous_pathname
        # Otherwise, return to the previous view mode normally
        return previous_view_mode or 'home', '/'
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

# Handle profile photo upload
@app.callback(
    [Output('profile-photo-display', 'src'),
     Output('profile-photo-display', 'style'),
     Output('profile-default-icon', 'style'),
     Output('upload-feedback', 'children'),
     Output('current-user-data', 'data', allow_duplicate=True)],
    [Input('upload-profile-photo', 'contents')],
    [State('session-store', 'data'),
     State('current-user-data', 'data')],
    prevent_initial_call=True
)
def upload_profile_photo(contents, session_data, current_user_data):
    """處理個人照片上傳"""
    if not contents or not session_data or 'session_id' not in session_data:
        raise PreventUpdate

    # Get user ID from session
    user_id = get_session(session_data['session_id'])
    if not user_id:
        return no_update, no_update, no_update, 'Session expired. Please login again.', no_update

    try:
        # Validate file type
        content_type, content_string = contents.split(',')

        # Check if it's an image
        if not content_type.startswith('data:image'):
            return no_update, no_update, no_update, 'Please upload an image file (JPG, PNG, etc.)', no_update

        # Decode the base64 data
        decoded = base64.b64decode(content_string)

        # Check file size (limit to 5MB)
        if len(decoded) > 5 * 1024 * 1024:
            return no_update, no_update, no_update, 'Image too large. Please upload an image smaller than 5MB.', no_update

        # Update database with photo data
        success, message = update_profile_photo(user_id, contents)

        if success:
            # Return updated styles to show photo and hide default icon
            photo_style = {
                'width': '150px',
                'height': '150px',
                'borderRadius': '50%',
                'objectFit': 'cover',
                'border': '3px solid #deb522',
                'display': 'block'
            }
            icon_style = {
                'fontSize': '6rem',
                'color': '#003580',
                'display': 'none'
            }

            # Update user data store to trigger avatar updates
            updated_user_data = current_user_data or {}
            updated_user_data['profile_photo'] = contents

            return contents, photo_style, icon_style, 'Photo uploaded successfully!', updated_user_data
        else:
            return no_update, no_update, no_update, f'Upload failed: {message}', no_update

    except Exception as e:
        return no_update, no_update, no_update, f'Error processing image: {str(e)}', no_update

# Update homepage user avatar when photo is uploaded
@app.callback(
    [Output('user-avatar-img', 'src'),
     Output('user-avatar-img', 'style'),
     Output('user-avatar-icon', 'style')],
    [Input('current-user-data', 'data'),
     Input('view-mode', 'data')]
)
def update_homepage_avatar(user_data, view_mode):
    """更新首頁使用者頭像"""
    # Only update when on homepage
    if view_mode != 'home':
        raise PreventUpdate

    # Update even if user_data is None (will show default icon)
    if not user_data:
        profile_photo = None
    else:
        profile_photo = user_data.get('profile_photo')

    if profile_photo:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'block'
        }
        icon_style = {'display': 'none'}
        return profile_photo, img_style, icon_style
    else:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'none'
        }
        icon_style = {'display': 'block'}
        return None, img_style, icon_style

# Update restaurant list page avatar
@app.callback(
    [Output('user-avatar-img-list', 'src'),
     Output('user-avatar-img-list', 'style'),
     Output('user-avatar-icon-list', 'style')],
    [Input('current-user-data', 'data'),
     Input('view-mode', 'data')]
)
def update_list_avatar(user_data, view_mode):
    """更新餐廳列表頁使用者頭像"""
    # Only update when on restaurant list page
    if view_mode != 'restaurant-list':
        raise PreventUpdate

    # Update even if user_data is None (will show default icon)
    if not user_data:
        profile_photo = None
    else:
        profile_photo = user_data.get('profile_photo')

    if profile_photo:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'block'
        }
        icon_style = {'display': 'none'}
        return profile_photo, img_style, icon_style
    else:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'none'
        }
        icon_style = {'display': 'block'}
        return None, img_style, icon_style

# Update hotel list page avatar
@app.callback(
    [Output('user-avatar-img-hotel-list', 'src'),
     Output('user-avatar-img-hotel-list', 'style'),
     Output('user-avatar-icon-hotel-list', 'style')],
    [Input('current-user-data', 'data'),
     Input('view-mode', 'data')]
)
def update_hotel_list_avatar(user_data, view_mode):
    """更新旅館列表頁使用者頭像"""
    # Only update when on hotel list page
    if view_mode != 'hotel-list':
        raise PreventUpdate

    # Update even if user_data is None (will show default icon)
    if not user_data:
        profile_photo = None
    else:
        profile_photo = user_data.get('profile_photo')

    if profile_photo:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'block'
        }
        icon_style = {'display': 'none'}
        return profile_photo, img_style, icon_style
    else:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'none'
        }
        icon_style = {'display': 'block'}
        return None, img_style, icon_style

# Update restaurant detail page avatar
@app.callback(
    [Output('user-avatar-img-detail', 'src'),
     Output('user-avatar-img-detail', 'style'),
     Output('user-avatar-icon-detail', 'style')],
    [Input('current-user-data', 'data'),
     Input('selected-restaurant-id', 'data')]
)
def update_detail_avatar(user_data, restaurant_id):
    """更新餐廳詳情頁使用者頭像"""
    # Only update when on restaurant detail page
    if not restaurant_id:
        raise PreventUpdate

    # Update even if user_data is None (will show default icon)
    if not user_data:
        profile_photo = None
    else:
        profile_photo = user_data.get('profile_photo')

    if profile_photo:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'block'
        }
        icon_style = {'display': 'none'}
        return profile_photo, img_style, icon_style
    else:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'none'
        }
        icon_style = {'display': 'block'}
        return None, img_style, icon_style

# Update hotel detail page avatar
@app.callback(
    [Output('user-avatar-img-hotel-detail', 'src'),
     Output('user-avatar-img-hotel-detail', 'style'),
     Output('user-avatar-icon-hotel-detail', 'style')],
    [Input('current-user-data', 'data'),
     Input('hotel-detail-data', 'data')]
)
def update_hotel_detail_avatar(user_data, hotel_data):
    """更新旅館詳情頁使用者頭像"""
    # Only update when on hotel detail page
    if not hotel_data:
        raise PreventUpdate

    # Update even if user_data is None (will show default icon)
    if not user_data:
        profile_photo = None
    else:
        profile_photo = user_data.get('profile_photo')

    if profile_photo:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'block'
        }
        icon_style = {'display': 'none'}
        return profile_photo, img_style, icon_style
    else:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'none'
        }
        icon_style = {'display': 'block'}
        return None, img_style, icon_style

# Update profile page avatar
@app.callback(
    [Output('user-avatar-img-profile', 'src'),
     Output('user-avatar-img-profile', 'style'),
     Output('user-avatar-icon-profile', 'style')],
    [Input('current-user-data', 'data'),
     Input('view-mode', 'data')]
)
def update_profile_page_avatar(user_data, view_mode):
    """更新個人檔案頁使用者頭像"""
    # Only update when on profile page
    if view_mode != 'profile':
        raise PreventUpdate

    # Update even if user_data is None (will show default icon)
    if not user_data:
        profile_photo = None
    else:
        profile_photo = user_data.get('profile_photo')

    if profile_photo:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'block'
        }
        icon_style = {'display': 'none'}
        return profile_photo, img_style, icon_style
    else:
        img_style = {
            'width': '40px',
            'height': '40px',
            'borderRadius': '50%',
            'objectFit': 'cover',
            'display': 'none'
        }
        icon_style = {'display': 'block'}
        return None, img_style, icon_style

# Navigate to profile page from restaurant detail page dropdown
@app.callback(
    [Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-view-mode', 'data', allow_duplicate=True),
     Output('selected-restaurant-id', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('menu-profile-detail', 'n_clicks')],
    [State('view-mode', 'data'),
     State('selected-restaurant-id', 'data'),
     State('url', 'pathname')],
    prevent_initial_call=True
)
def navigate_to_profile_from_restaurant_detail(n_clicks, current_view_mode, restaurant_id_data, current_pathname):
    """從餐廳詳細頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        # Keep restaurant ID and store the current pathname to return to the same restaurant detail page
        # Set previous-view-mode to 'restaurant-detail' to indicate we came from a detail page
        return 'profile', 'restaurant-detail', restaurant_id_data, '/'
    raise PreventUpdate

# Navigate to profile page from hotel detail page dropdown
@app.callback(
    [Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-view-mode', 'data', allow_duplicate=True),
     Output('previous-pathname', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('menu-profile-hotel-detail', 'n_clicks')],
    [State('view-mode', 'data'),
     State('url', 'pathname')],
    prevent_initial_call=True
)
def navigate_to_profile_from_hotel_detail(n_clicks, current_view_mode, current_pathname):
    """從旅館詳細頁下拉選單導航到個人檔案頁"""
    if n_clicks:
        # Store the current pathname to return to the same hotel detail page
        # Set previous-view-mode to 'hotel-detail' to indicate we came from a detail page
        return 'profile', 'hotel-detail', current_pathname, '/'
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
# 自动搜索：当输入关键字或选择旅馆类型时自动触发搜索
@app.callback(
    [Output('hotel-search-results-store', 'data'),
     Output('hotel-current-page-store', 'data')],
    [Input('search-hotel', 'value'),
     Input('search-hotel-type', 'data')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def handle_hotel_list_search(keyword, hotel_type, view_mode):
    """處理旅館列表頁搜尋（自動搜尋，與餐廳搜尋功能相同）"""
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
                html.I(className='fas fa-hotel', style={'fontSize': '4rem', 'color': '#003580', 'marginBottom': '2rem'}),
                html.H3('No hotels found', style={'color': '#1A1A1A'}),
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

        # 安全處理 Rating (防止 None 值)
        rating = hotel.get('Rating', 0)
        rating_text = f"{rating:.1f}" if rating is not None else "N/A"

        # 安全處理 UserRatingsTotal (防止 None 值)
        user_ratings_total = hotel.get('UserRatingsTotal', 0)
        reviews_count = int(user_ratings_total) if user_ratings_total is not None else 0

        card_content = html.Div([
            html.Img(
                src='/assets/food_dirtyrice.png',
                style={'width': '100%', 'height': '200px', 'objectFit': 'cover', 'borderRadius': '8px 8px 0 0'}
            ),
            html.Div([
                html.Div(hotel['HotelName'], style={'color': '#1A1A1A', 'fontSize': '1.2rem', 'fontWeight': 'bold', 'marginBottom': '0.5rem'}),
                html.Div(types_text, style={'color': '#003580', 'fontSize': '0.9rem', 'marginBottom': '0.5rem'}),
                html.Div([
                    html.Span([
                        html.I(className='fas fa-star', style={'color': '#003580', 'marginRight': '5px'}),
                        rating_text
                    ], style={'marginRight': '1rem'}),
                    html.Span([
                        html.I(className='fas fa-comment', style={'color': '#888', 'marginRight': '5px'}),
                        f"{reviews_count} reviews"
                    ])
                ], style={'color': '#aaaaaa', 'fontSize': '0.85rem', 'marginBottom': '0.5rem'}),
                html.Div([
                    html.I(className='fas fa-map-marker-alt', style={'marginRight': '5px'}),
                    hotel['Address'][:40] + '...' if len(hotel['Address']) > 40 else hotel['Address']
                ], style={'color': '#888888', 'fontSize': '0.85rem'})
            ], style={'padding': '1rem'})
        ], style={
            'backgroundColor': '#F2F6FA',
            'borderRadius': '8px',
            'overflow': 'hidden',
            'border': '1.5px solid #D0D5DD',
            'transition': 'transform 0.2s, border-color 0.2s',
            'cursor': 'pointer',
            'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
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
    [Output('selected-restaurant-id', 'data', allow_duplicate=True),
     Output('previous-page-location', 'data', allow_duplicate=True)],
    [Input('url', 'pathname')],
    prevent_initial_call=True
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
            raise PreventUpdate
    else:
        raise PreventUpdate

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

    print(f"DEBUG: load_hotel_detail_data triggered for pathname={pathname}, hotel_id={hotel_id}")

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

# Callback 4: Card Click Handler - 處理餐廳卡片點擊事件 (修正版)
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-page-location', 'data', allow_duplicate=True)], # 確保有這個 Output
    [Input({'type': 'restaurant-card', 'index': ALL}, 'n_clicks')],
    [State({'type': 'restaurant-card', 'index': ALL}, 'id'),
     State('view-mode', 'data')], # 讀取當前頁面模式
    prevent_initial_call=True
)
def handle_card_click(n_clicks_list, card_ids, current_view_mode):
    ctx = callback_context
    # 檢查是否有有效點擊
    if not ctx.triggered or not any(n for n in n_clicks_list if n is not None and n > 0):
        raise PreventUpdate

    try:
        triggered_prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
        triggered_id = json.loads(triggered_prop_id)
        
        # 確保是點擊餐廳卡片
        if triggered_id.get('type') != 'restaurant-card':
            raise PreventUpdate
            
        restaurant_id = triggered_id['index']

        # [關鍵修正] 判斷來源
        # 預設來自列表
        prev_loc = {'from': 'restaurant-list'} 
        
        # 如果當前 view-mode 是 analytics，就標記來源為 analytics
        if current_view_mode == 'analytics':
            prev_loc = {'from': 'analytics'}

        return f'/restaurant/{restaurant_id}', None, prev_loc
        
    except Exception as e:
        print(f"Error in handle_card_click: {e}")
        raise PreventUpdate

# Callback 4b: Nearby Restaurant Card Click Handler - 處理附近餐廳卡片點擊事件
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('view-mode', 'data', allow_duplicate=True)],
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

    # 導航到詳細頁面，清除 view-mode 讓 URL 路由優先
    return f'/restaurant/{restaurant_id}', None

# 5. Back Button Handler - 處理餐廳詳細頁返回按鈕 (修正版)
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('view-mode', 'data', allow_duplicate=True),
     Output('from-map-navigation', 'data', allow_duplicate=True)],
    [Input('restaurant-detail-back-btn', 'n_clicks')],
    [State('previous-page-location', 'data'),
     State('from-map-navigation', 'data')],
    prevent_initial_call=True
)
def handle_back_button(n_clicks, previous_page, from_map):
    if not n_clicks:
        raise PreventUpdate

    # [關鍵修正] 優先檢查是否來自 Analytics
    if previous_page and previous_page.get('from') == 'analytics':
        # URL 改回首頁 (停止顯示詳細頁)，並將模式切回 analytics
        return '/', 'analytics', False

    # 處理來自地圖導航的情況
    if from_map:
        return '/#distribution-map-section', 'home', False

    # 預設回到餐廳列表
    return '/restaurant-list', 'restaurant-list', False

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
    [Output('user-dropdown-hotel-detail', 'className'),
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

# Callback 8: Logout from Restaurant Detail Page - 從餐廳詳細頁面登出
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout-detail', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_restaurant_detail_page(n_clicks, session_data):
    """從餐廳詳細頁面下拉選單登出"""
    if not n_clicks:
        raise PreventUpdate

    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])

    return None

# Callback 8b: Logout from Hotel Detail Page - 從旅館詳細頁面登出
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout-hotel-detail', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_hotel_detail_page(n_clicks, session_data):
    """從旅館詳細頁面下拉選單登出"""
    if not n_clicks:
        raise PreventUpdate

    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])

    return None

# 點擊星等長條圖顯示該星級部分評論，並提供 Show all 按鈕
@app.callback(
    [Output('reviews-comments', 'children'),
     Output('selected-rating-store', 'data')],
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
            return html.Div('Unable to parse clicked rating', style={'color': '#888888'}), None

        matched = [r for r in reviews if r and r.get('rating') is not None and int(round(float(r['rating']))) == clicked_star]

        if not matched:
            return html.Div(f'No comments for {clicked_star}★', style={'color': '#888888'}), clicked_star

        items = []
        for r in matched[:6]:
            text = r.get('comment') or 'No comment text'
            items.append(html.Div([
                html.Div(f"★ {clicked_star}", style={'color': '#003580', 'fontWeight': '600', 'marginRight': '8px', 'display': 'inline-block', 'width': '48px'}),
                html.Div(text, style={'color': '#1A1A1A', 'display': 'inline-block', 'verticalAlign': 'top', 'maxWidth': 'calc(100% - 60px)'})
            ], style={'padding': '8px 0', 'borderBottom': '1px solid #222', 'animation': 'fadeIn 0.3s ease'}))

        # Add Show all button if more comments exist
        if len(matched) > 6:
            items.append(html.Div([
                html.Button('Show all comments', id={'type': 'show-all-comments', 'index': clicked_star}, n_clicks=0, className='btn-primary', style={'marginTop': '10px'})
            ], style={'textAlign': 'center'}))

        return html.Div(items), clicked_star

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
            return html.Div(f'No comments for {star}★', style={'color': '#888888'}), star

        items = []
        for r in matched:
            text = r.get('comment') or 'No comment text'
            items.append(html.Div([
                html.Div(f"★ {star}", style={'color': '#003580', 'fontWeight': '600', 'marginRight': '8px', 'display': 'inline-block', 'width': '48px'}),
                html.Div(text, style={'color': '#1A1A1A', 'display': 'inline-block', 'verticalAlign': 'top', 'maxWidth': 'calc(100% - 60px)'})
            ], style={'padding': '8px 0', 'borderBottom': '1px solid #222', 'animation': 'fadeIn 0.3s ease'}))

        return html.Div(items), star

# Callback to update bar chart colors when a rating is selected
@app.callback(
    Output('ratings-bar-chart', 'figure', allow_duplicate=True),
    [Input('selected-rating-store', 'data')],
    [State('restaurant-detail-data', 'data'),
     State('hotel-detail-data', 'data')],
    prevent_initial_call=True
)
def update_bar_chart_selection(selected_rating, restaurant_data, hotel_data):
    """Update bar chart colors to highlight the selected rating."""
    # Choose which detail data to use (restaurant preferred)
    detail_data = None
    if isinstance(restaurant_data, dict) and restaurant_data:
        detail_data = restaurant_data
    elif isinstance(hotel_data, dict) and hotel_data:
        detail_data = hotel_data
    else:
        raise PreventUpdate

    # Get reviews and count ratings
    reviews = detail_data.get('reviews', []) if isinstance(detail_data, dict) else []
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for review in reviews:
        try:
            rating = review.get('rating')
            if rating is None:
                continue
            rating_int = int(round(float(rating)))
            if 1 <= rating_int <= 5:
                counts[rating_int] += 1
        except Exception:
            continue

    ratings = list(counts.keys())
    values = [counts[r] for r in ratings]

    # Create colors array - highlight selected bar
    colors = []
    for r in ratings:
        if selected_rating is not None and r == selected_rating:
            colors.append('#ffd700')  # Brighter gold for selected
        else:
            colors.append('#deb522')  # Normal gold

    # Create updated bar chart
    fig = px.bar(
        x=ratings,
        y=values,
        labels={'x': 'Stars', 'y': 'Count'},
        title='Ratings distribution',
        text=values,
        height=360
    )

    # Update with dynamic colors
    fig.update_traces(
        marker_color=colors,
        marker_line_color='#ffffff',
        marker_line_width=2 if selected_rating is not None else 0,
        hovertemplate='<b>%{x} Stars</b><br>Count: %{y}<br><i>Click to view reviews</i><extra></extra>',
        hoverlabel=dict(
            bgcolor='#2a2a2a',
            font_size=14,
            font_family='Segoe UI, Arial',
            font_color='#ffffff',
            bordercolor='#003580'
        )
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title={
            'text': f'Ratings distribution - <i>{"Showing " + str(selected_rating) + "★ reviews" if selected_rating else "Click on any bar to view reviews"}</i>',
            'x': 0.02,
            'xanchor': 'left',
            'font': {'color': '#1A1A1A', 'size': 16}
        },
        xaxis=dict(
            tickfont=dict(color='#ffffff', size=12),
            title=dict(text='Stars', font=dict(color='#003580', size=14))
        ),
        yaxis=dict(
            tickfont=dict(color='#ffffff', size=12),
            title=dict(text='Count', font=dict(color='#003580', size=14))
        ),
        margin=dict(l=60, r=20, t=60, b=60),
        hovermode='closest',
        transition=dict(duration=200, easing='cubic-in-out'),
        uirevision='constant'  # Prevent full re-render, only update data
    )

    return fig

##########################################################
####  旅館詳細頁面 Callbacks (Hotel Detail Page)  ####
##########################################################

# Callback 1: Handle hotel card click
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-page-location', 'data', allow_duplicate=True)], # 新增 output (請確認 store id 正確)
    [Input({'type': 'hotel-card', 'index': ALL}, 'n_clicks')],
    [State({'type': 'hotel-card', 'index': ALL}, 'id'),
     State('view-mode', 'data')],
    prevent_initial_call=True
)
def handle_hotel_card_click(n_clicks_list, card_ids, current_view):
    ctx = callback_context
    if not ctx.triggered or not any(n for n in n_clicks_list if n is not None):
        raise PreventUpdate

    try:
        triggered_prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
        triggered_id = json.loads(triggered_prop_id)
        hotel_id = triggered_id['index']

        # [關鍵] 判斷來源
        prev_loc = {'from': 'hotel-list'} # 預設 (旅館原本可能沒有這個store邏輯，現在統一加上)
        if current_view == 'analytics':
            prev_loc = {'from': 'analytics'}
        # 注意：你需要確保有 previous-page-location 這個 Store
        # 如果 hotel 原本用 from-map-navigation，這裡最好統一用 previous-page-location

        return f'/hotel/{hotel_id}', None, prev_loc
    except: raise PreventUpdate

# Callback 3: Render hotel detail content when hotel-detail-data store is populated
@app.callback(
    Output('hotel-detail-content', 'children'),
    [Input('hotel-detail-data', 'data')],
    prevent_initial_call=True
)
def render_hotel_detail(hotel_data):
    """根據 hotel-detail-data store 渲染旅館詳細內容（與餐廳流程一致）"""
    print("DEBUG: render_hotel_detail called")
    if not hotel_data:
        print("DEBUG: hotel_data empty")
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
                            'backgroundColor': '#FBC02D',
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
                            html.Div(nearby['HotelName'], style={'color': '#1A1A1A', 'fontWeight': '600'}),
                            html.Div([
                                html.Span([
                                    html.I(className='fas fa-star', style={'color': '#003580', 'marginRight': '4px'}),
                                    f"{nearby['Rating']:.1f}"
                                ], style={'marginRight': '12px'}),
                                html.Span(f"{nearby['distance']:.2f} km", style={'color': '#888'})
                            ], style={'fontSize': '0.85rem', 'marginTop': '4px'})
                        ])
                    ], style={'display': 'flex', 'alignItems': 'center', 'padding': '12px',
                             'backgroundColor': '#F2F6FA', 'border': '1.5px solid #D0D5DD',
                             'borderRadius': '8px', 'marginBottom': '8px', 'cursor': 'pointer',
                             'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.05)'})
                ], id={'type': 'nearby-hotel-card', 'index': nearby['Hotel_ID']}, n_clicks=0)
                nearby_cards.append(card)
            
            return html.Div([
                html.H4([
                    html.I(className='fas fa-hotel', style={'marginRight': '8px', 'color': '#003580'}),
                    f'Nearby Hotels ({len(nearby_hotels)})'
                ], style={'color': '#1A1A1A', 'fontSize': '1.1rem', 'marginBottom': '1rem'}),
                html.Div(nearby_cards)
            ], style={
                'backgroundColor': '#F2F6FA',
                'border': '1.5px solid #D0D5DD',
                'borderRadius': '12px',
                'padding': '1.5rem',
                'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.08)'
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
# Callback 6: Handle back button (Hotel) - 修正轉圈圈問題
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('from-map-navigation', 'data', allow_duplicate=True),
     Output('view-mode', 'data', allow_duplicate=True)], # 新增 view-mode 輸出
    [Input('hotel-detail-back-btn', 'n_clicks')],
    [State('from-map-navigation', 'data'),
     State('previous-page-location', 'data')], # 加入這個 State
    prevent_initial_call=True
)
def handle_hotel_back_button(n_clicks, from_map, previous_page):
    """處理旅館詳情頁返回按鈕"""
    if not n_clicks:
        raise PreventUpdate

    # [關鍵修正] 如果是從 analytics 來的
    if previous_page and previous_page.get('from') == 'analytics':
        # URL 必須變回根目錄 '/'，否則 display_page 會一直以為還在 hotel 頁面
        return '/', False, 'analytics'

    # If came from map
    if from_map:
        return '/#distribution-map-section', False, 'home'
    
    # Default back to list
    return '/', False, 'hotel-list'

##########################################################

# ====== Attraction Callbacks ======

# Callback 1: Handle attraction card click
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input({'type': 'attraction-card', 'index': ALL}, 'n_clicks')],
    [State({'type': 'attraction-card', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def handle_attraction_card_click(n_clicks_list, card_ids):
    """處理景點卡片點擊，導航到詳細頁面"""
    ctx = callback_context

    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_dict = json.loads(triggered_id)
    attraction_id = triggered_dict['index']

    print(f"DEBUG: Attraction card clicked! attraction_id={attraction_id}")

    return f'/attraction/{attraction_id}'

# Callback 2: Store attraction search results
@app.callback(
    [Output('attraction-search-results-store', 'data'),
     Output('attraction-current-page-store', 'data', allow_duplicate=True)],
    [Input('search-attraction', 'value'),
     Input('selected-attraction-type', 'data'),
     Input('selected-attraction-rating', 'data')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def search_and_store_attractions(keyword, attr_type, rating_range, view_mode):
    """執行景點搜尋並存儲結果"""
    if view_mode != 'attraction-list':
        raise PreventUpdate

    # Parse rating range
    min_rating = None
    max_rating = None
    if rating_range:
        if rating_range == '4-5':
            min_rating, max_rating = 4.0, 5.0
        elif rating_range == '3-4':
            min_rating, max_rating = 3.0, 4.0
        elif rating_range == '2-3':
            min_rating, max_rating = 2.0, 3.0
        elif rating_range == '1-2':
            min_rating, max_rating = 1.0, 2.0

    # Search attractions with filters
    df = search_attractions(
        keyword=keyword,
        attr_type=attr_type,
        min_rating=min_rating,
        max_rating=max_rating,
        sort_by='rating_desc'
    )

    # Convert to dict for storage
    results = df.to_dict('records') if not df.empty else []

    # Reset to page 1 when search changes
    return results, 1

# Callback 3: Update attraction grid and pagination
@app.callback(
    [Output('attraction-grid', 'children'),
     Output('attraction-pagination-controls', 'children'),
     Output('attraction-search-stats', 'children')],
    [Input('attraction-search-results-store', 'data'),
     Input('attraction-current-page-store', 'data')],
    prevent_initial_call=False
)
def update_attraction_grid(search_results, current_page):
    """更新景點網格和分頁控制"""
    if search_results is None:
        # Initial load, fetch default results
        df = search_attractions(sort_by='rating_desc')
        search_results = df.to_dict('records')

    if not search_results:
        return (
            html.Div([
                html.I(className='fas fa-landmark',
                      style={'fontSize': '4rem', 'color': '#003580', 'marginBottom': '2rem'}),
                html.H3('No attractions found', style={'color': '#1A1A1A', 'marginBottom': '1rem'}),
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

    # Create attraction cards
    cards = []
    for attraction in current_items:
        card = create_attraction_card(attraction)
        cards.append(card)

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
    stats = f"Showing {start_idx + 1}-{end_idx} of {total_items} attractions"

    return grid, pagination, stats

# Callback 4: Toggle attraction type dropdown
@app.callback(
    Output('attraction-type-dropdown-menu', 'style'),
    [Input('attraction-type-trigger', 'n_clicks'),
     Input('attraction-type-icon', 'n_clicks')],
    [State('attraction-type-dropdown-menu', 'style')],
    prevent_initial_call=True
)
def toggle_attraction_type_dropdown(trigger_clicks, icon_clicks, current_style):
    """切換景點類型下拉選單"""
    is_open = current_style.get('display') == 'block'
    return {'display': 'none'} if is_open else {'display': 'block'}

# Callback 5: Handle attraction type selection
@app.callback(
    [Output('selected-attraction-type', 'data'),
     Output('attraction-type-selected-text', 'children'),
     Output('attraction-type-dropdown-menu', 'style', allow_duplicate=True)],
    [Input({'type': 'attraction-type-option', 'index': ALL}, 'n_clicks')],
    [State({'type': 'attraction-type-option', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def handle_attraction_type_selection(n_clicks_list, option_ids):
    """處理景點類型選擇"""
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    import json as _json
    selected_option = _json.loads(triggered_id)
    selected_index = selected_option['index']

    if selected_index == '__CLEAR__':
        return None, 'Attraction Type', {'display': 'none'}
    else:
        return selected_index, selected_index, {'display': 'none'}

# Callback 6: Toggle attraction rating dropdown
@app.callback(
    Output('attraction-rating-dropdown-menu', 'style'),
    [Input('attraction-rating-trigger', 'n_clicks'),
     Input('attraction-rating-icon', 'n_clicks')],
    [State('attraction-rating-dropdown-menu', 'style')],
    prevent_initial_call=True
)
def toggle_attraction_rating_dropdown(trigger_clicks, icon_clicks, current_style):
    """切換景點評分下拉選單"""
    is_open = current_style.get('display') == 'block'
    return {'display': 'none'} if is_open else {'display': 'block'}

# Callback 7: Handle attraction rating selection
@app.callback(
    [Output('selected-attraction-rating', 'data'),
     Output('attraction-rating-selected-text', 'children'),
     Output('attraction-rating-dropdown-menu', 'style', allow_duplicate=True)],
    [Input({'type': 'attraction-rating-option', 'index': ALL}, 'n_clicks')],
    [State({'type': 'attraction-rating-option', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def handle_attraction_rating_selection(n_clicks_list, option_ids):
    """處理景點評分選擇"""
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    import json as _json
    selected_option = _json.loads(triggered_id)
    selected_index = selected_option['index']

    if selected_index == '__CLEAR__':
        return None, 'Rating', {'display': 'none'}
    else:
        # Map rating range to display text
        rating_text_map = {
            '4-5': '⭐⭐⭐⭐⭐ 4~5 Stars',
            '3-4': '⭐⭐⭐⭐ 3~4 Stars',
            '2-3': '⭐⭐⭐ 2~3 Stars',
            '1-2': '⭐⭐ 1~2 Stars'
        }
        display_text = rating_text_map.get(selected_index, 'Rating')
        return selected_index, display_text, {'display': 'none'}

# ====== Attraction Detail Page Callbacks ======

# Toggle user dropdown on attraction detail page
@app.callback(
    [Output('user-dropdown-attraction-detail', 'className'),
     Output('dropdown-open-detail', 'data', allow_duplicate=True)],
    [Input('user-avatar-attraction-detail', 'n_clicks')],
    [State('dropdown-open-detail', 'data')],
    prevent_initial_call=True
)
def toggle_user_dropdown_attraction_detail(n_clicks, is_open):
    """Toggle user dropdown menu on attraction detail page"""
    if n_clicks:
        new_state = not is_open
        className = 'user-dropdown show' if new_state else 'user-dropdown'
        return className, new_state
    raise PreventUpdate

# Navigate to profile from attraction detail page
@app.callback(
    [Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-view-mode', 'data', allow_duplicate=True),
     Output('previous-pathname', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('menu-profile-attraction-detail', 'n_clicks')],
    [State('view-mode', 'data'),
     State('url', 'pathname')],
    prevent_initial_call=True
)
def navigate_to_profile_from_attraction_detail(n_clicks, current_view_mode, current_pathname):
    """Navigate to profile page from attraction detail page dropdown"""
    if n_clicks:
        # Store the current pathname to return to the same attraction detail page
        # Set previous-view-mode to 'attraction-detail' to indicate we came from a detail page
        return 'profile', 'attraction-detail', current_pathname, '/'
    raise PreventUpdate

# Logout from attraction detail page
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout-attraction-detail', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_attraction_detail(n_clicks, session_data):
    """Logout from attraction detail page dropdown"""
    if not n_clicks:
        raise PreventUpdate
    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])
    return None

# Handle back button from attraction detail page
@app.callback(
    [Output('view-mode', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('attraction-detail-back-btn', 'n_clicks')],
    [State('view-mode', 'data')],
    prevent_initial_call=True
)
def navigate_back_from_attraction_detail(n_clicks, current_view_mode):
    """Navigate back from attraction detail page to attraction list"""
    if n_clicks:
        return 'attraction-list', '/'
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
    elif selected_map == 'attractions':
        return create_attraction_map_chart()
    return html.Div()

# ===== Callback: Restaurant Map Click Navigation =====
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('from-map-navigation', 'data', allow_duplicate=True)],
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

        # Navigate to restaurant detail page and mark that we came from map
        return f'/restaurant/{int(restaurant_id)}', True
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error handling restaurant map click: {e}")
        print(f"Click data: {click_data}")
        raise PreventUpdate

# ===== Callback: Hotel Map Click Navigation =====
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('from-map-navigation', 'data', allow_duplicate=True)],
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

        # Navigate to hotel detail page and mark that we came from map
        return f'/hotel/{int(hotel_id)}', True
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error handling hotel map click: {e}")
        print(f"Click data: {click_data}")
        raise PreventUpdate

# ===== Callback: Attraction Map Click Navigation =====
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('from-map-navigation', 'data', allow_duplicate=True)],
    Input('attraction-map-graph', 'clickData'),
    prevent_initial_call=True
)
def navigate_from_attraction_map(click_data):
    if click_data is None:
        raise PreventUpdate

    try:
        # Extract Attraction ID from customdata
        attraction_id = click_data['points'][0]['customdata'][0]
        print(f"Attraction map clicked - ID: {attraction_id}")  # Debug log

        # Navigate to attraction detail page and mark that we came from map
        return f'/attraction/{int(attraction_id)}', True
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error handling attraction map click: {e}")
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

# ===== Clientside Callback: Scroll to Map Section on Hash Navigation =====
app.clientside_callback(
    """
    function(pathname) {
        // Check if URL contains hash for distribution map section
        if (pathname && pathname.includes('#distribution-map-section')) {
            setTimeout(function() {
                const mapSection = document.getElementById('distribution-map-section');
                if (mapSection) {
                    mapSection.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }, 300);  // Wait for page to render
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('distribution-map-section', 'className'),
    Input('url', 'pathname')
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
                    'user-dropdown-detail',
                    'user-dropdown-hotel-detail',
                    'user-dropdown-attraction-list'
                ];

                const avatarIds = [
                    'user-avatar',
                    'user-avatar-list',
                    'user-avatar-hotel-list',
                    'user-avatar-detail',
                    'user-avatar-hotel-detail',
                    'user-avatar-attraction-list'
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

def create_traffic_map_chart(points=None):
    """Creates a mapbox scatter plot of all restaurants and hotels."""
    # Get restaurant data
    df_restaurants = get_all_restaurants()
    df_restaurants = df_restaurants.dropna(subset=['Lat', 'Long'])
    df_restaurants['type'] = 'Restaurant'

    # Get hotel data
    df_hotels = get_all_hotels()
    df_hotels = df_hotels.dropna(subset=['Lat', 'Long'])
    df_hotels['type'] = 'Hotel'

    # Get attraction data
    df_attractions = get_all_attractions()
    df_attractions = df_attractions.dropna(subset=['Lat', 'Long'])
    df_attractions['type'] = 'Attraction'

    # Rename HotelName to Name for consistency and combine dataframes
    df_combined = pd.concat([
        df_restaurants[['Name', 'Lat', 'Long', 'type']],
        df_hotels[['HotelName', 'Lat', 'Long', 'type']].rename(columns={'HotelName': 'Name'}),
        df_attractions[['Name', 'Lat', 'Long', 'type']]
    ])

    # Add emojis to the 'type' column for legend and hover
    df_combined['type_emoji'] = df_combined['type'].map({
        'Restaurant': '🍔 Restaurant',
        'Hotel': '🏨 Hotel',
        'Attraction': '🗼 Attraction'
    })

    fig = px.scatter_map(
        df_combined,
        lat="Lat",
        lon="Long",
        hover_name="Name",
        color="type_emoji", # Use the new column with emojis for coloring/legend
        color_discrete_map={
            "🍔 Restaurant": "#32CD32",  # Green
            "🏨 Hotel": "#FF6347",       # Red
            "🗼 Attraction": "#8A2BE2"   # Blue Violet for Attractions
        },
        zoom=11,
        center={"lat": 35.0116, "lon": 135.7681},
        height=600,
        map_style="carto-positron",
        custom_data=['Name', 'type']
    )
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=True,
        legend_title_text='Type',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(0, 53, 128, 0.5)',
            font=dict(
                color='white'
            )
        ),
        clickmode='event+select',
        hoverdistance=20,
        uirevision='constant' # Add this line to preserve map state
    )
    fig.update_traces(
        marker=dict(
            size=12,
            opacity=0.9
        ),
        hoverlabel=dict(
            bgcolor='#003580',
            font_size=14,
            font_family='Arial, sans-serif'
        )
    )
    return dcc.Graph(
        id='traffic-map-graph',
        figure=fig,
        config={
            'displayModeBar': True,
            'scrollZoom': True,
            'doubleClick': 'reset',
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
    )
# Add this helper function after the create_traffic_map_chart function (around line 2750)



# Callback: Toggle between text and map calculators
@app.callback(
    [Output('text-calculator-section', 'style'),
     Output('map-calculator-section', 'style'),
     Output('toggle-text-calculator', 'color'),
     Output('toggle-map-calculator', 'color'),
     Output('active-calculator', 'data')],
    [Input('toggle-text-calculator', 'n_clicks'),
     Input('toggle-map-calculator', 'n_clicks')],
    [State('active-calculator', 'data')],
    prevent_initial_call=True
)
def toggle_calculator_mode(text_clicks, map_clicks, current_mode):
    """Toggle between text-based and map-based distance calculators"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'toggle-text-calculator':
        # Show text calculator, hide map calculator
        return (
            {'padding': '2rem'},  # Show text section
            {'display': 'none'},  # Hide map section
            'primary',  # Text button active
            'secondary',  # Map button inactive
            'text'  # Update active mode
        )
    else:  # toggle-map-calculator
        # Show map calculator, hide text calculator
        return (
            {'display': 'none'},  # Hide text section
            {'padding': '2rem'},  # Show map section
            'secondary',  # Text button inactive
            'primary',  # Map button active
            'map'  # Update active mode
        )


# Add Store for place names at the top of app.layout (around line 1560)
# Add this line inside the app.layout = html.Div([ ... ]) section:
dcc.Store(id='all-places-store', data=load_all_place_names(), storage_type='memory'),
# Find this callback (around line 2870) and modify the RETURN statement at the end:
@app.callback(
    [Output('traffic-map-store', 'data'),
     Output('distance-calculation-result', 'children')],
    [Input('traffic-map-graph', 'clickData')],
    [State('traffic-map-store', 'data')],
    prevent_initial_call=True
)
def handle_distance_calculation(click_data, store_data):
    if click_data is None:
        raise PreventUpdate
    
    # Initialize store_data if it's None
    if store_data is None:
        store_data = {'points': []}
    
    points = store_data.get('points', [])
    
    try:
        clicked_point = click_data['points'][0]
        lat = clicked_point['lat']
        lon = clicked_point['lon']
        name = clicked_point.get('customdata', ['Unknown'])[0] if clicked_point.get('customdata') else 'Unknown Point'
        
    except (KeyError, IndexError, TypeError):
        error_div = html.Div(
            "⚠ Error: Could not extract point. Please click directly on a marker.", 
            style={
                'color': '#FF0000', 
                'fontWeight': 'bold', 
                'padding': '20px',
                'textAlign': 'center',
                'fontSize': '1.2rem',
                'backgroundColor': '#FFE6E6',
                'borderRadius': '8px',
                'border': '2px solid #FF0000'
            }
        )
        return {'points': points}, error_div

    points.append({'lat': lat, 'lon': lon, 'name': name})

    if len(points) == 1:
        result = html.Div([
            html.Div("✅", style={'fontSize': '3rem', 'textAlign': 'center', 'marginBottom': '1rem'}),
            html.H3(
                "First Point Selected", 
                style={'color': '#32CD32', 'textAlign': 'center', 'marginBottom': '1rem'}
            ),
            html.P(
                f"{name}", 
                style={'fontSize': '1.2rem', 'fontWeight': 'bold', 'textAlign': 'center', 'color': '#1A1A1A', 'marginBottom': '1rem'}
            ),
            html.P(
                "First point selected. Click on another point to calculate distance", 
                style={'color': '#666', 'textAlign': 'center', 'fontSize': '1.1rem'}
            )
        ], style={
            'backgroundColor': '#F0FFF4',
            'padding': '2rem',
            'borderRadius': '8px',
            'border': '2px solid #32CD32'
        })
        return {'points': points}, result
    
    elif len(points) >= 2:
        p1 = points[0]
        p2 = points[1]
        
        try:
            # Haversine distance calculation
            R = 6371
            lat1, lon1, lat2, lon2 = float(p1['lat']), float(p1['lon']), float(p2['lat']), float(p2['lon'])
            lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(np.radians, [lat1, lon1, lat2, lon2])
            
            dlon = lon2_rad - lon1_rad
            dlat = lat2_rad - lat1_rad
            a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
            c = 2 * np.arcsin(np.sqrt(a))
            distance = R * c
            
            google_maps_url = f"https://www.google.com/maps/dir/?api=1&origin={lat1},{lon1}&destination={lat2},{lon2}&travelmode=transit"
            
            result_content = html.Div([
                html.Div("🎯", style={'fontSize': '3rem', 'textAlign': 'center', 'marginBottom': '1rem'}),
                html.H3("Route Calculated!", style={'color': '#003580', 'textAlign': 'center', 'marginBottom': '2rem'}),
                
                # From/To display
                html.Div([
                    html.Div([
                        html.Span("📍", style={'fontSize': '1.5rem'}),
                        html.Strong("From: ", style={'color': '#1A1A1A', 'fontSize': '1.1rem'}),
                        html.Span(p1['name'], style={'color': '#1A1A1A', 'fontSize': '1.1rem'})
                    ], style={'marginBottom': '1rem', 'textAlign': 'center'}),
                    html.Div([
                        html.Span("📍", style={'fontSize': '1.5rem'}),
                        html.Strong("To: ", style={'color': '#1A1A1A', 'fontSize': '1.1rem'}),
                        html.Span(p2['name'], style={'color': '#1A1A1A', 'fontSize': '1.1rem'})
                    ], style={'marginBottom': '2rem', 'textAlign': 'center'}),
                ]),
                
                # Distance
                html.Div([
                    html.Div("Straight-Line Distance:", style={'fontSize': '1.5rem', 'marginBottom': '0.5rem'}),
                    html.Div(f"{distance:.2f} km", style={
                        'fontSize': '2.5rem',
                        'fontWeight': 'bold',
                        'color': '#003580',
                        'marginBottom': '0.5rem'
                    }),
                    html.Div([
                        html.I(className='fas fa-info-circle', style={'marginRight': '8px'}),
                        "Click 'View Directions' below for actual travel distance & time"
                    ], style={
                        'fontSize': '0.9rem',
                        'color': '#666',
                        'fontStyle': 'italic',
                        'marginBottom': '2rem'
                    })
                ], style={'textAlign': 'center'}),
                
                # Google Maps button
                html.Div([
                    html.A([
                        html.I(className='fas fa-directions', style={'marginRight': '10px', 'fontSize': '1.2rem'}),
                        'View Directions on Google Maps'
                    ], href=google_maps_url, target="_blank", style={
                        'display': 'inline-block',
                        'padding': '15px 30px',
                        'backgroundColor': '#4285f4',
                        'color': 'white',
                        'textDecoration': 'none',
                        'borderRadius': '8px',
                        'fontWeight': '600',
                        'fontSize': '1.1rem',
                        'boxShadow': '0 4px 6px rgba(66, 133, 244, 0.3)',
                        'transition': 'all 0.3s'
                    })
                ], style={'textAlign': 'center', 'marginBottom': '2rem'}),
                
                html.Div("Click two new points for another route", style={
                    'textAlign': 'center',
                    'fontSize': '0.9rem',
                    'color': '#888',
                    'fontStyle': 'italic'
                })
            ], style={
                'backgroundColor': '#E6F3FF',
                'padding': '2rem',
                'borderRadius': '8px',
                'border': '2px solid #003580'
            })
            
            # CHANGE THIS LINE - keep points with value 2 to hide instruction
            return {'points': []}, result_content# Changed from {'points': []} to keep the 2 points
            
        except (ValueError, TypeError) as e:
            error_result = html.Div(
                f"❌ Error: {str(e)}", 
                style={
                    'color': '#FF0000', 
                    'fontWeight': 'bold', 
                    'textAlign': 'center', 
                    'fontSize': '1.2rem',
                    'backgroundColor': '#FFE6E6',
                    'padding': '2rem',
                    'borderRadius': '8px',
                    'border': '2px solid #FF0000'
                }
            )
            return {'points': []}, error_result
    
    default_result = html.Div(
        f"Selected {len(points)} point. Click another point.", 
        style={
            'color': '#1A1A1A', 'textAlign': 'center', 
            'fontSize': '1.1rem',
            'padding': '2rem',
            'backgroundColor': '#F0F0F0',
            'borderRadius': '8px',
            'border': '2px solid #CCC'
        }
    )
    return {'points': points}, default_result
# Add this callback after the existing traffic-related callbacks (around line 2924)
# Replace the previous callback with this corrected version:
@app.callback(
    [Output('point-selection-instruction', 'children'),
     Output('point-selection-instruction', 'style')],
    Input('traffic-map-store', 'data')
)
def update_point_instruction(store_data):  # â† Removed the extra parameter
    if store_data is None:
        store_data = {'points': []}
    
    points = store_data.get('points', [])
    
    base_style = {
        'padding': '1.5rem',
        'borderRadius': '8px',
        'marginBottom': '1.5rem'
    }
    
    if len(points) == 0:
        # No points selected yet - show blue instruction
        content = html.Div([
            html.Div([
                html.I(className='fas fa-map-marker-alt', style={'marginRight': '10px', 'fontSize': '1.5rem', 'color': '#003580'}),
                html.Span("Step 1: Select your first point on the map", style={'fontSize': '1.2rem', 'fontWeight': '600', 'color': '#003580'})
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '10px'}),
            html.P("Click on any restaurant or hotel marker to begin", style={'textAlign': 'center', 'color': '#666', 'fontSize': '1rem', 'marginBottom': '0'})
        ])
        style = {
            **base_style,
            'backgroundColor': '#E6F3FF',
            'border': '2px solid #003580',
            'animation': 'pulse 2s ease-in-out infinite'
        }
        return content, style
        
    elif len(points) == 1:
        # First point selected - show green success message
        content = html.Div([
            html.Div([
                html.I(className='fas fa-check-circle', style={'marginRight': '10px', 'fontSize': '1.5rem', 'color': '#32CD32'}),
                html.Span("Step 2: Select your destination point", style={'fontSize': '1.2rem', 'fontWeight': '600', 'color': '#32CD32'})
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '10px'}),
            html.P(f"First point: {points[0]['name']}", style={'textAlign': 'center', 'color': '#1A1A1A', 'fontSize': '1rem', 'fontWeight': '500', 'marginBottom': '5px'}),
            html.P("Click on another marker to calculate distance", style={'textAlign': 'center', 'color': '#666', 'fontSize': '1rem', 'marginBottom': '0'})
        ])
        style = {
            **base_style,
            'backgroundColor': '#F0FFF4',
            'border': '2px solid #32CD32'
        }
        return content, style
    
# ==========================================
#  Advanced Analytics Interactive Callbacks
# ==========================================

# Helper: 計算兩點距離 (Haversine)
# Helper: 計算兩點距離 (Haversine) - 修復版
# ==========================================
#  Helper Function: 計算兩點距離 (Haversine)
# ==========================================
def calculate_distances(df, center_lat, center_lon):
    """計算 DataFrame 中所有點與中心點的距離 (km)"""
    import numpy as np # 確保 numpy 有被引入
    R = 6371  # 地球半徑 (km)
    
    # 確保資料是數值型態，並處理 NaN
    try:
        lat2 = pd.to_numeric(df['Lat'], errors='coerce').fillna(0)
        lon2 = pd.to_numeric(df['Long'], errors='coerce').fillna(0)
        
        # 將角度轉為弧度
        lat1_rad = np.radians(float(center_lat))
        lon1_rad = np.radians(float(center_lon))
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        # 防止浮點數誤差導致 sqrt 內出現負數
        a = np.clip(a, 0, 1)
        
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c
    except Exception as e:
        print(f"Error in calculate_distances: {e}")
        return pd.Series([9999] * len(df)) # 發生錯誤時回傳大距離，避免崩潰

# ==========================================
#  Sync Map Click to Search Dropdown
# ==========================================
@app.callback(
    Output('analytics-attraction-search', 'value'),
    Input('interactive-map', 'clickData'),
    State('analytics-attraction-search', 'value'),
    prevent_initial_call=True
)
def sync_map_click_to_dropdown(click_data, current_search_value):
    """當點擊地圖景點時，更新下拉選單"""
    if not click_data: raise PreventUpdate
    try:
        point = click_data['points'][0]
        # 檢查是否點到景點 (customdata[1] == 'Attraction')
        if 'customdata' in point and len(point['customdata']) > 1:
            p_id = point['customdata'][0]
            p_type = point['customdata'][1]
            
            if p_type == 'Attraction' and p_id != current_search_value:
                return p_id
    except Exception: pass
    raise PreventUpdate

# ==========================================
#  Advanced Analytics Callback (Final Logic Fix)
# ==========================================
@app.callback(
    [Output('interactive-map', 'figure'),
     Output('cp-matrix-graph', 'figure'),
     Output('matrix-status-text', 'children'),
     Output('analytics-list-content', 'children'),
     Output('analytics-attraction-info', 'children')], 
    [Input('analytics-attraction-search', 'value'), # 直接監聽 Dropdown
     Input('interactive-map', 'relayoutData'),           
     Input('interactive-map', 'selectedData'),           
     Input('analytics-type-filter', 'value'),
     Input('analytics-tabs', 'active_tab')],
    [State('analytics-combined-data', 'data'),
     State('interactive-map', 'figure')]                 
)
def update_analytics_dashboard(search_id, relayout_data, selected_data, type_filter, active_tab, data, current_fig):
    try:
        if not data: return no_update, no_update, "Loading...", html.Div("Loading..."), None
        df = pd.DataFrame(data)
        if df.empty: return no_update, no_update, "No data.", html.Div("No data."), None

        # 預處理
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.1)
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)

        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'init'

        full_df = df.copy() # 保留完整資料用於計算距離
        filtered_df = df.copy() # 這是最後要顯示在地圖上的資料
        
        map_center = {"lat": 35.0116, "lon": 135.7681} 
        map_zoom = 11
        status_msg = "Explore mode: Drag map or search to filter."
        target_point = None 
        is_focus_mode = False
        attraction_info_card = None 

        # --- 1. 篩選邏輯 ---
        if search_id:
            # 找到目標點
            target = df[(df['ID'] == search_id) & (df['Type'] == 'Attraction')]
            if not target.empty:
                target_point = target.iloc[0]
                is_focus_mode = True
        
        # 如果進入聚焦模式 (Focus Mode)
        if is_focus_mode and target_point is not None:
            t_lat, t_lon = target_point['Lat'], target_point['Long']
            
            # [關鍵修復 1]：在 "完整 df" 上計算距離，保留所有周邊資料
            full_df['dist'] = calculate_distances(full_df, t_lat, t_lon)
            
            # 篩選 2km 內的資料
            filtered_df = full_df[full_df['dist'] <= 2.0].copy()
            
            map_center = {"lat": t_lat, "lon": t_lon}
            map_zoom = 13.5
            status_msg = f"🎯 Focused on {target_point['Name']} (2km radius)"

            # 產生景點資訊卡
            sub_cat = target_point.get('SubCategory') or 'Tourist Attraction'
            attraction_info_card = dbc.Card([
                dbc.CardBody([
                    html.H4([html.I(className="fas fa-map-marker-alt me-2", style={'color':'#d9534f'}), target_point['Name']], className="card-title"),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([html.Strong("Type: "), html.Span(sub_cat), html.Br(), html.Strong("Rating: "), html.Span(f"⭐ {target_point['Rating']}")], width=6),
                        dbc.Col([html.Strong("Location: "), html.Span(f"{t_lat:.4f}, {t_lon:.4f}")], width=6),
                    ]),
                ])
            ], className="shadow-sm", style={'borderLeft': '5px solid #d9534f', 'backgroundColor': '#fff5f5'})

        # 手動框選邏輯
        elif trigger_id == 'interactive-map' and selected_data and 'points' in selected_data:
             try:
                df['temp_key'] = df['ID'].astype(str) + '_' + df['Type']
                selected_keys = [f"{p['customdata'][0]}_{p['customdata'][1]}" for p in selected_data['points'] if 'customdata' in p]
                if selected_keys:
                    filtered_df = df[df['temp_key'].isin(selected_keys)]
                    status_msg = f"Selected {len(filtered_df)} items manually"
             except: pass

        # 移動邏輯 (只有在非 Focus 模式下才生效)
        elif trigger_id == 'interactive-map' and relayout_data and not is_focus_mode:
            if 'mapbox._derived' in relayout_data and 'coordinates' in relayout_data['mapbox._derived']:
                coords = relayout_data['mapbox._derived']['coordinates']
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                filtered_df = df[
                    (df['Lat'] >= min(lats)) & (df['Lat'] <= max(lats)) &
                    (df['Long'] >= min(lons)) & (df['Long'] <= max(lons))
                ]
                status_msg = "Filtering by current map view"
            if 'mapbox.center' in relayout_data:
                map_center = relayout_data['mapbox.center']
            if 'mapbox.zoom' in relayout_data:
                map_zoom = relayout_data['mapbox.zoom']

        # --- 2. 產生地圖 ---
        color_map = {'Restaurant': '#32CD32', 'Hotel': '#FF4500', 'Attraction': '#9370DB', 'Unknown': '#888888'}
        
        fig_map = px.scatter_mapbox(
            filtered_df, lat="Lat", lon="Long", color="Type", size="Rating", size_max=12,
            hover_name="Name", hover_data={"ID":True, "Type":True, "Price":True}, 
            color_discrete_map=color_map, zoom=map_zoom, center=map_center, height=500
        )
        if target_point is not None:
            fig_map.add_trace(go.Scattermapbox(
                lat=[target_point['Lat']], lon=[target_point['Long']], mode='markers+text',
                marker=go.scattermapbox.Marker(size=25, color='red', opacity=0.9),
                text=[target_point['Name']], textposition="top center", name='Target'
            ))
        fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0}, clickmode='event+select', uirevision='constant')

        # --- 3. 產生矩陣 ---
        if type_filter is None: type_filter = []
        matrix_df = filtered_df[filtered_df['Type'].isin(type_filter)]
        matrix_df = matrix_df[matrix_df['Price'] > 0]

        if matrix_df.empty:
            fig_matrix = px.scatter(title="No matching data")
            fig_matrix.update_layout(xaxis={'visible': False}, yaxis={'visible': False})
        else:
            fig_matrix = px.scatter(
                matrix_df, x="Price", y="Rating", color="Type", hover_name="Name",
                size="Rating", color_discrete_map=color_map, template="plotly_white", height=450
            )
            try:
                avg_price = matrix_df['Price'].median()
                fig_matrix.add_vline(x=avg_price, line_dash="dash", line_color="gray", annotation_text="Median")
                fig_matrix.add_hline(y=4.0, line_dash="dash", line_color="green", annotation_text="High Rating")
            except: pass

        # --- 4. 產生詳細列表 ---
        list_content = []
        target_type = 'Restaurant' if active_tab == 'tab-analytics-restaurants' else 'Hotel'
        
        # [關鍵修復 2]：分開計算 CP 值，避免飯店被過濾光
        type_df = matrix_df[matrix_df['Type'] == target_type].copy()
        
        list_df = pd.DataFrame()
        if not type_df.empty:
            # 針對該類型計算平均價
            type_avg_price = type_df['Price'].mean()
            
            # 篩選 High CP (評分高 且 價格 < 平均價 * 1.5) -> 放寬一點係數
            recommendations = type_df[(type_df['Rating'] >= 4.0) & (type_df['Price'] <= type_avg_price * 1.5)]
            
            if recommendations.empty: 
                recommendations = type_df[type_df['Rating'] >= 3.8] # 如果沒結果，放寬到 3.8 分
            if recommendations.empty:
                recommendations = type_df # 還是沒結果，顯示全部
            
            list_df = recommendations.sort_values('Rating', ascending=False)
        
        if list_df.empty:
            list_content = html.Div([
                html.I(className="fas fa-search", style={'fontSize':'2rem', 'color':'#ccc', 'marginBottom':'10px'}),
                html.P(f"No {target_type.lower()}s found nearby.", style={'color':'#888'})
            ], style={'textAlign':'center', 'padding':'20px'})
        else:
            cards = []
            for _, row in list_df.head(8).iterrows():
                try:
                    if target_type == 'Restaurant':
                        r_data = {'Restaurant_ID': row['ID'], 'Name': row['Name'], 'FirstCategory': row['SubCategory'], 'TotalRating': row['Rating']}
                        # 🔥 [關鍵修復 3]：明確傳入 ID 類型，讓導航 Callback 能夠捕捉！
                        cards.append(create_destination_card(r_data, id_type='analytics-restaurant-card'))
                    else:
                        h_data = {'Hotel_ID': row['ID'], 'HotelName': row['Name'], 'Types': [row['SubCategory']], 'Rating': row['Rating'], 'Address': 'Kyoto'}
                        # 🔥 [關鍵修復 3]：明確傳入 ID 類型
                        cards.append(create_hotel_card(h_data, id_type='analytics-hotel-card'))
                except: pass

            list_content = html.Div(cards, style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fill, minmax(300px, 1fr))', 'gap': '1.5rem'})

        return fig_map, fig_matrix, status_msg, list_content, attraction_info_card

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return px.scatter(), px.scatter(), "Error", html.Div("System Error"), None
    
# =========================================================
#  NEW: Analytics Navigation Logic (Fix Back Button)
# =========================================================

@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-page-location', 'data', allow_duplicate=True)], 
    [Input({'type': 'analytics-restaurant-card', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def handle_analytics_restaurant_click(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered or not any(n for n in n_clicks_list if n is not None and n > 0):
        raise PreventUpdate

    try:
        triggered_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
        restaurant_id = triggered_id['index']
        # 強制設定來源
        return f'/restaurant/{restaurant_id}', None, {'from': 'analytics'}
    except: raise PreventUpdate

@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('view-mode', 'data', allow_duplicate=True),
     Output('previous-page-location', 'data', allow_duplicate=True)], 
    [Input({'type': 'analytics-hotel-card', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def handle_analytics_hotel_click(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered or not any(n for n in n_clicks_list if n is not None and n > 0):
        raise PreventUpdate

    try:
        triggered_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
        hotel_id = triggered_id['index']
        # 強制設定來源
        return f'/hotel/{hotel_id}', None, {'from': 'analytics'}
    except: raise PreventUpdate

# ===== Text-Based Distance Calculator Callbacks =====

# Callback 1: Populate dropdown options with place names
# Find the populate_location_dropdowns callback (around line 3175) and replace it with this improved version:

@app.callback(
    [Output('traffic-start-location', 'options'),
     Output('traffic-end-location', 'options')],
    Input('all-places-store', 'data')
)
def populate_location_dropdowns(places_data):
    """Populate both dropdown menus with all available places"""
    if not places_data:
        return [], []
    
    options = []
    for place in places_data:
        # Create label with name and type emoji
        type_emoji = {
            'Restaurant': '🍔',
            'Hotel': '🏨',
            'Attraction': '🗼'
        }.get(place['type'], '📍')
        
        name = place['name']
        
        # Truncate long names to prevent squeezing
        # If name is longer than 40 characters, truncate and add ellipsis
        display_name = name if len(name) <= 40 else name[:37] + '...'
        
        # Create readable label with proper spacing
        label = f"{type_emoji} {display_name}"
        value = f"{place['type']}_{place['id']}"  # Unique identifier
        
        options.append({'label': label, 'value': value})
    
    # Sort alphabetically
    options = sorted(options, key=lambda x: x['label'])
    
    return options, options

# Add this callback after the populate_location_dropdowns callback (around line 3185)

@app.callback(
    [Output('traffic-start-location', 'options', allow_duplicate=True),
     Output('traffic-end-location', 'options', allow_duplicate=True)],
    [Input('traffic-start-location', 'search_value'),
     Input('traffic-end-location', 'search_value')],
    [State('all-places-store', 'data')],
    prevent_initial_call=True
)
def filter_location_options(start_search, end_search, places_data):
    """Filter dropdown options based on user's search input"""
    if not places_data:
        return [], []
    
    # Determine which input triggered the callback
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Create base options list
    def create_options(filter_text=None):
        options = []
        for place in places_data:
            # Apply filter if provided
            if filter_text and len(filter_text) >= 2:
                filter_lower = filter_text.lower()
                if filter_lower not in place['name'].lower() and filter_lower not in place['type'].lower():
                    continue
            
            type_emoji = {
                'Restaurant': '🍔',
                'Hotel': '🏨',
                'Attraction': '🗼'
            }.get(place['type'], '📍')
            
            name = place['name']
            display_name = name if len(name) <= 40 else name[:37] + '...'
            label = f"{type_emoji} {display_name}"
            value = f"{place['type']}_{place['id']}"
            options.append({'label': label, 'value': value})
        
        return sorted(options, key=lambda x: x['label'])
    
    # Only update the dropdown that triggered the search
    if trigger_id == 'traffic-start-location':
        # Filter start location options based on start_search
        start_options = create_options(start_search if start_search and len(start_search) >= 2 else None)
        # Keep end location unchanged
        return start_options, no_update
    else:
        # Filter end location options based on end_search
        end_options = create_options(end_search if end_search and len(end_search) >= 2 else None)
        # Keep start location unchanged
        return no_update, end_options

# Callback 2: Calculate distance between text-selected locations
@app.callback(
    Output('text-distance-result', 'children'),
    Input('calculate-text-distance-btn', 'n_clicks'),
    [State('traffic-start-location', 'value'),
     State('traffic-end-location', 'value'),
     State('all-places-store', 'data')],
    prevent_initial_call=True
)
def calculate_text_distance(n_clicks, start_value, end_value, places_data):
    """Calculate distance between two text-selected locations"""
    if not n_clicks or not start_value or not end_value:
        return html.Div([
            html.I(className='fas fa-info-circle', 
                  style={'fontSize': '2rem', 'color': '#888', 'marginBottom': '1rem'}),
            html.P('Select both starting point and destination, then click Calculate', 
                  style={'color': '#888', 'textAlign': 'center'})
        ], style={'textAlign': 'center', 'padding': '2rem'})
    
    if start_value == end_value:
        return html.Div([
            html.I(className='fas fa-exclamation-triangle', 
                  style={'fontSize': '2rem', 'color': '#FFA500', 'marginBottom': '1rem'}),
            html.P('Please select two different locations', 
                  style={'color': '#FFA500', 'textAlign': 'center', 'fontWeight': 'bold'})
        ], style={'textAlign': 'center', 'padding': '2rem'})
    
    # Parse the values to get type and ID
    try:
        start_type, start_id = start_value.split('_', 1)
        end_type, end_id = end_value.split('_', 1)
    except:
        return html.Div('Error parsing locations', style={'color': '#FF0000'})
    
    # Find the selected places in the data
    start_place = None
    end_place = None
    
    for place in places_data:
        place_value = f"{place['type']}_{place['id']}"
        if place_value == start_value:
            start_place = place
        if place_value == end_value:
            end_place = place
    
    if not start_place or not end_place:
        return html.Div('Could not find selected locations', style={'color': '#FF0000'})
    
    # Calculate distance using Haversine formula
    try:
        R = 6371  # Earth radius in km
        lat1, lon1 = float(start_place['lat']), float(start_place['lon'])
        lat2, lon2 = float(end_place['lat']), float(end_place['lon'])
        
        lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(np.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
        c = 2 * np.arcsin(np.sqrt(a))
        distance = R * c
        
        # Create Google Maps directions URL
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&origin={lat1},{lon1}&destination={lat2},{lon2}&travelmode=transit"
        
        # Build result display
        type_emoji_map = {'Restaurant': '🍔', 'Hotel': '🏨', 'Attraction': '🗼'}
        
        return html.Div([
            html.Div("🎯", style={'fontSize': '3rem', 'textAlign': 'center', 'marginBottom': '1rem'}),
            
            # From/To display
            html.Div([
                html.Div("Route Calculated!",  style={'fontSize': '2.5rem','color': '#003580', 'textAlign': 'center', 'marginBottom': '2rem'}),
                html.Div([
                    html.Span(type_emoji_map.get(start_place['type'], 'ðŸ"'), 
                             style={'fontSize': '1.5rem', 'marginRight': '8px'}),
                    html.Strong("From: ", style={'color': '#1A1A1A'}),
                    html.Span(start_place['name'], style={'color': '#666'})
                ], style={'marginBottom': '0.5rem', 'textAlign': 'center'}),
                
                
                html.Div([
                    html.Span(type_emoji_map.get(end_place['type'], 'ðŸ"'), 
                             style={'fontSize': '1.5rem', 'marginRight': '8px'}),
                    html.Strong("To: ", style={'color': '#1A1A1A'}),
                    html.Span(end_place['name'], style={'color': '#666'})
                ], style={'marginBottom': '1.5rem', 'textAlign': 'center'}),
            ]),
            
            # Distance display
            html.Div([
                html.Div("Straight-Line Distance:", 
                        style={'fontSize': '1.2rem', 'color': '#666', 'marginBottom': '0.5rem'}),
                html.Div(f"{distance:.2f} km", style={
                    'fontSize': '2.5rem',
                    'fontWeight': 'bold',
                    'color': '#003580',
                    'marginBottom': '1.5rem'
                })
            ], style={'textAlign': 'center'}),
            
            # Google Maps button
            html.Div([
                html.A([
                    html.I(className='fas fa-directions', 
                          style={'marginRight': '10px', 'fontSize': '1.2rem'}),
                    'Get Directions on Google Maps'
                ], href=google_maps_url, target="_blank", style={
                    'display': 'inline-block',
                    'padding': '12px 24px',
                    'backgroundColor': '#4285f4',
                    'color': 'white',
                    'textDecoration': 'none',
                    'borderRadius': '8px',
                    'fontWeight': '600',
                    'boxShadow': '0 4px 6px rgba(66, 133, 244, 0.3)',
                    'transition': 'all 0.3s'
                })
            ], style={'textAlign': 'center'})
            
        ], style={
            'backgroundColor': '#F0F8FF',
            'padding': '2rem',
            'borderRadius': '8px',
            'border': '2px solid #003580'
        })
        
    except Exception as e:
        return html.Div([
            html.I(className='fas fa-exclamation-circle', 
                  style={'fontSize': '2rem', 'color': '#FF0000', 'marginBottom': '1rem'}),
            html.P(f'Error calculating distance: {str(e)}', 
                  style={'color': '#FF0000', 'textAlign': 'center'})
        ], style={'textAlign': 'center', 'padding': '2rem'})
    
# 1. 處理愛心點擊 (Toggle Favorite)
@app.callback(
    Output({'type': 'fav-btn', 'item_type': MATCH, 'index': MATCH}, 'children'),
    Input({'type': 'fav-btn', 'item_type': MATCH, 'index': MATCH}, 'n_clicks'),
    State({'type': 'fav-btn', 'item_type': MATCH, 'index': MATCH}, 'id'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def toggle_favorite_state(n_clicks, btn_id, session_data):
    if not session_data or 'session_id' not in session_data:
        raise PreventUpdate # 未登入不處理
        
    # 這裡需要從 session_id 換取 user_id (假設 session_data 裡有 user_id)
    # 如果你的 session_data 只有 session_id，你需要用 get_session(session_id)
    user_id = get_session(session_data['session_id']) 
    
    if not user_id: raise PreventUpdate

    item_type = btn_id['item_type']
    item_id = btn_id['index']
    
    # 呼叫 DB 更新狀態
    from utils.database import toggle_favorite_db
    is_fav = toggle_favorite_db(user_id, item_id, item_type)
    
    # 更新圖示
    icon_cls = "fas fa-heart" if is_fav else "far fa-heart"
    color = "#ff4757" if is_fav else "white"
    
    return html.I(className=icon_cls, style={'color': color, 'fontSize': '1.2rem'})

# 2. 首頁收藏區內容切換
@app.callback(
    [Output('fav-tab-rest', 'className'),
     Output('fav-tab-hotel', 'className'),
     Output('fav-tab-attr', 'className'),
     Output('favorites-content-container', 'children')],
    [Input('fav-tab-rest', 'n_clicks'),
     Input('fav-tab-hotel', 'n_clicks'),
     Input('fav-tab-attr', 'n_clicks')],
    State('session-store', 'data')
)
def update_favorites_section(btn1, btn2, btn3, session_data):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'fav-tab-rest'
    
    active_cls = 'tab-item active'
    base_cls = 'tab-item'
    
    target_type = 'Restaurant'
    c1, c2, c3 = active_cls, base_cls, base_cls
    
    if trigger_id == 'fav-tab-hotel':
        target_type = 'Hotel'
        c1, c2, c3 = base_cls, active_cls, base_cls
    elif trigger_id == 'fav-tab-attr':
        target_type = 'Attraction'
        c1, c2, c3 = base_cls, base_cls, active_cls
        
    # 獲取資料
    content = html.Div("Please login to see favorites.", style={'textAlign':'center', 'padding':'2rem'})
    
    if session_data and 'session_id' in session_data:
        user_id = get_session(session_data['session_id'])
        if user_id:
            # 從 DB 撈取該用戶的所有收藏 ID
            from utils.database import get_user_favorites
            favs = get_user_favorites(user_id) # 回傳 {'Restaurant': [ids], ...}
            ids = favs.get(target_type, [])
            
            if not ids:
                content = html.Div(f"No favorite {target_type.lower()}s yet.", style={'textAlign':'center', 'color':'#888'})
            else:
                # 根據 ID 撈取詳細資料並生成卡片
                cards = []
                for iid in ids:
                    try:
                        if target_type == 'Restaurant':
                            data = get_restaurant_by_id(iid)
                            if data: cards.append(create_destination_card(dict(data), is_favorite=True))
                        elif target_type == 'Hotel':
                            data = get_hotel_by_id(iid)
                            if data: cards.append(create_hotel_card(dict(data), is_favorite=True))
                        elif target_type == 'Attraction':
                            data = get_attraction_by_id(iid)
                            if data: cards.append(create_attraction_card(dict(data), is_favorite=True))
                    except: pass
                
                content = html.Div(cards, className='card-row') # 橫向滾動
                content = html.Div(content, className='card-scroll-container')
                
    return c1, c2, c3, content

# 3. Planner: 更新左側來源清單 (Source List)
# [FIX 5] Planner: 更新左側來源清單 (確保按鈕 ID 結構簡單)
@app.callback(
    Output("planner-source-list", "children"),
    [Input("planner-tabs", "active_tab"),
     Input('session-store', 'data')]
)
def update_planner_source(active_tab, session_data):
    if not session_data or 'session_id' not in session_data: 
        return html.Div("Please login to see favorites.", className="text-center p-4")
    
    user_id = get_session(session_data['session_id'])
    items_ui = []
    
    if active_tab == "tab-plan-fav":
        from utils.database import get_user_favorites
        favs = get_user_favorites(user_id) 
        
        for cat, ids in favs.items():
            if not ids: continue
            
            # 建立分類標題
            items_ui.append(html.H6(f"{cat}s", className="mt-3 mb-2 text-primary border-bottom pb-1"))
            
            for iid in ids:
                name = f"{cat} #{iid}" 
                try:
                    int_id = int(iid) # 確保轉型
                    item_data = None
                    
                    if cat == 'Restaurant': item_data = get_restaurant_by_id(int_id)
                    elif cat == 'Hotel': item_data = get_hotel_by_id(int_id)
                    elif cat == 'Attraction': item_data = get_attraction_by_id(int_id)
                    
                    if item_data:
                        # 統一取 Name 欄位 (因為我们在 initialize_database 統一了欄位名)
                        name = item_data.get('Name') or item_data.get('HotelName') or name

                        items_ui.append(
                            dbc.Card([
                                dbc.CardBody([
                                    html.Div(name, style={'fontWeight':'bold', 'fontSize':'0.9rem', 'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis'}),
                                    # [重點] 按鈕 ID 只包含 type, index, cat。不包含 name。
                                    dbc.Button("Add", 
                                               id={'type': 'add-to-plan', 'index': str(int_id), 'cat': cat}, 
                                               size="sm", color="primary", outline=True, className="mt-2 w-100", style={'fontSize':'0.8rem'})
                                ], className="p-2")
                            ], className="mb-2 shadow-sm")
                        )
                except: continue
                
    elif active_tab == "tab-plan-rec":
        items_ui = [html.Div("System recommendations will appear here.", className="text-muted text-center p-4")]

    return items_ui

# 4. Planner: 處理 "Add" 和 "Remove" 與 "Add Day" (更新右側行程)
# [FIX 2 & 3] Planner 邏輯修正：配合新的 ID 結構
@app.callback(
    Output("trip-plan-data", "data"),
    [Input({'type': 'add-to-plan', 'index': ALL, 'cat': ALL}, 'n_clicks'), # [修正] 這裡拿掉 name 和 id，改用 index
     Input({'type': 'remove-plan-item', 'day': ALL, 'idx': ALL}, 'n_clicks'),
     Input({'type': 'remove-day-btn', 'day': ALL}, 'n_clicks'),
     Input('add-day-btn', 'n_clicks')],
    [State("trip-plan-data", "data")],
    prevent_initial_call=True
)
def update_trip_data(add_clicks, remove_item_clicks, remove_day_clicks, add_day_click, current_data):
    ctx = callback_context
    if not ctx.triggered: raise PreventUpdate
    
    trigger_prop_id = ctx.triggered[0]['prop_id']
    trigger_value = ctx.triggered[0]['value']
    
    if not trigger_value or trigger_value == 0: raise PreventUpdate

    trigger_id_str = trigger_prop_id.split('.')[0]
    if not current_data: current_data = {'days': [{'day': 1, 'items': []}]}
    
    # CASE 1: 新增天數
    if trigger_id_str == 'add-day-btn':
        new_day_num = len(current_data['days']) + 1
        current_data['days'].append({'day': new_day_num, 'items': []})
        return current_data
        
    try:
        trigger_obj = json.loads(trigger_id_str)
    except: raise PreventUpdate

    # CASE 2: 加入項目
    if trigger_obj.get('type') == 'add-to-plan':
        item_cat = trigger_obj['cat']
        item_id = trigger_obj['index']
        item_name = "Unknown Item"

        # 重新查詢名稱 (因為 ID 裡沒放名稱了)
        try:
            int_id = int(item_id)
            if item_cat == 'Restaurant': 
                res = get_restaurant_by_id(int_id)
                if res: item_name = res.get('Name')
            elif item_cat == 'Hotel': 
                res = get_hotel_by_id(int_id)
                if res: item_name = res.get('Name') # 資料庫已統一名稱
            elif item_cat == 'Attraction': 
                res = get_attraction_by_id(int_id)
                if res: item_name = res.get('Name')
        except: pass
        
        if not current_data['days']:
             current_data['days'] = [{'day': 1, 'items': []}]
             
        current_data['days'][-1]['items'].append({
            'name': item_name,
            'cat': item_cat,
            'id': item_id
        })
        
    # CASE 3: 移除項目
    elif trigger_obj.get('type') == 'remove-plan-item':
        day_num = trigger_obj['day']
        item_idx = trigger_obj['idx']
        for d in current_data['days']:
            if d['day'] == day_num:
                if 0 <= item_idx < len(d['items']):
                    d['items'].pop(item_idx)
                break

    # CASE 4: 移除整天
    elif trigger_obj.get('type') == 'remove-day-btn':
        day_to_remove = trigger_obj['day']
        current_data['days'] = [d for d in current_data['days'] if d['day'] != day_to_remove]
        for i, d in enumerate(current_data['days']):
            d['day'] = i + 1
        if not current_data['days']:
             current_data['days'] = [{'day': 1, 'items': []}]

    return current_data

# 5. Planner: 渲染右側行程表 (View)
# [FIX 3] Planner: 渲染右側行程表 (加入刪除天數按鈕)
@app.callback(
    Output("planner-itinerary-view", "children"),
    Input("trip-plan-data", "data")
)
def render_trip_itinerary(data):
    if not data or not data.get('days'): 
        return html.Div("Start adding items!", className="text-center text-muted mt-5")
    
    days_ui = []
    for day in data.get('days', []):
        day_num = day['day']
        items = day['items']
        
        item_list = []
        for idx, item in enumerate(items):
            icon = "fas fa-utensils" if item['cat'] == 'Restaurant' else "fas fa-hotel" if item['cat'] == 'Hotel' else "fas fa-torii-gate"
            item_list.append(
                dbc.ListGroupItem([
                    dbc.Row([
                        dbc.Col([html.I(className=f"{icon} me-2 text-muted"), html.Span(item['name'])], width=10),
                        dbc.Col(
                            dbc.Button(html.I(className="fas fa-times"), 
                                       id={'type': 'remove-plan-item', 'day': day_num, 'idx': idx},
                                       color="danger", outline=True, size="sm", className="border-0"), 
                            width=2, className="text-end"
                        )
                    ], align="center")
                ])
            )
        
        # Day Card Header with Delete Button
        header_content = dbc.Row([
            dbc.Col(html.Span(f"Day {day_num}", className="fw-bold"), width=8),
            dbc.Col(
                dbc.Button(html.I(className="fas fa-trash-alt"), 
                           id={'type': 'remove-day-btn', 'day': day_num},
                           color="danger", outline=True, size="sm", className="float-end"),
                width=4
            )
        ], align="center")

        days_ui.append(
            dbc.Card([
                dbc.CardHeader(header_content, className="bg-light"),
                dbc.ListGroup(item_list, flush=True) if item_list else dbc.CardBody("No items yet.", className="text-muted small p-2")
            ], className="mb-3 shadow-sm")
        )
        
    return days_ui

# [MISSING] 點擊首頁 "Create a Trip" 按鈕 -> 進入 /create-trip
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('create-trip-btn', 'n_clicks'),
    prevent_initial_call=True
)
def navigate_to_create_trip(n_clicks):
    if n_clicks:
        return '/create-trip'
    return no_update

# [FIX 4] 處理 Trip Planner 頁面上的返回按鈕 (修正 NoneType 錯誤)
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input({'type': 'back-btn', 'index': 'planner'}, 'n_clicks'),
    prevent_initial_call=True
)
def go_back_from_planner(n_clicks):
    # 修正：先確認 n_clicks 不是 None，且大於 0
    if n_clicks:
        return '/'
    return no_update
    
if __name__ == '__main__':
    app.run(debug=True, port=8050)