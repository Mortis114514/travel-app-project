# Import 所有相關套件
import dash
from dash import Dash, html, dcc, Input, State, Output, dash_table, no_update, callback_context, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import dash_leaflet as dl
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import uuid
import random
import json
from datetime import datetime, timedelta

# 從./utils導入所有自定義函數
from utils.const import get_constants, TAB_STYLE, ALL_COMPARE_METRICS
from utils.data_clean import travel_data_clean, countryinfo_data_clean, data_merge
from utils.auth import verify_user, create_user, get_session, create_session, delete_session, clean_expired_sessions
from pages.login_page import create_login_layout, create_register_layout
from utils.data_transform import (
    prepare_country_compare_data, 
    get_dashboard_default_values, 
    get_alert_rank, 
    sanitize_cost_bounds, 
    filter_by_cost_and_types, 
    preprocess_travel_df,
    pick_country_level,
    filter_by_alert_and_visa,
    compute_scores,
)
from utils.visualization import (
    build_compare_figure, 
    generate_stats_card, 
    generate_bar, 
    generate_pie, 
    generate_map, 
    generate_box,
    build_table_component
)

########################
#### 資料載入與前處理 ####
########################
# 加載欲分析的資料集
# travel_df = pd.read_csv('./data/Travel_dataset.csv')  # 旅遊資訊 (Legacy - 已停用)
# country_info_df = pd.read_csv('./data/country_info.csv')  # 國家資訊 (Legacy - 已停用)
# attractions_df = pd.read_csv('./data/Attractions.csv')  # 景點資訊 (Legacy - 已停用)
restaurants_df = pd.read_csv('./data/Kyoto_Restaurant_Info_Full.csv')  # 餐廳資訊 (現行使用)

# 進行資料前處理 (Legacy - 已停用)
# travel_df = travel_data_clean(travel_df)
# country_info_df = countryinfo_data_clean(country_info_df)

# 合併 travel_df 和 country_info_df，方便後續分析 (Legacy - 已停用)
# df_merged = data_merge(travel_df, country_info_df)

# 呼叫 ./utils/const.py 中的 get_constants() 函式（畫面上方四格統計）(Legacy - 已停用)
# num_of_country, num_of_traveler, num_of_nationality, avg_days = get_constants(travel_df)

# 獲取國家名稱列表（景點頁使用）(Legacy - 已停用)
# country_list = list(attractions_df['country'].unique())

# 設定 Overview 頁面預設值 (Legacy - 已停用)
# DEFAULTS = get_dashboard_default_values(df_merged)

# 切換頁面（如有需要可以自行增加）
def load_data(tab):
    if tab in ('travel', 'planner'):
        return df_merged

# 隨機選擇4-5星餐廳
def get_random_top_restaurants(n=5):
    """從4-5星餐廳中隨機選擇n個餐廳"""
    top_restaurants = restaurants_df[restaurants_df['Rating_Category'] == '4~5 星餐廳'].copy()
    if len(top_restaurants) >= n:
        return top_restaurants.sample(n=n)
    else:
        return top_restaurants

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
    """創建料理類型選項列表（包含清除選項）"""
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
    # 其他選項
    for cat in sorted(restaurants_df['FirstCategory'].dropna().unique()):
        options.append(
            html.Div(remove_parentheses(cat),
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
    """創建目的地卡片 (使用餐廳資料)"""
    return html.Div([
        html.Img(
            src='/assets/Hazuki.jpg',  # 使用相同圖片作為佔位符
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

def create_saved_trip_card(trip_data):
    """創建已存行程卡片"""
    return html.Div([
        html.Img(
            src='/assets/Hazuki.jpg',
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

def create_inspiration_card(article):
    """創建靈感文章卡片"""
    return html.Div([
        html.Img(
            src='/assets/Hazuki.jpg',
            className='inspiration-image'
        ),
        html.Div([
            html.Div(article['title'], className='inspiration-title'),
            html.Div(article['category'], className='inspiration-category')
        ], className='inspiration-overlay')
    ], className='inspiration-card')

def create_compound_search_bar():
    """創建優化的複合式搜尋欄（帶即時建議和進階篩選）"""
    return html.Div([
        # Main search bar
        html.Div([
            html.Div([
                html.I(className='fas fa-search'),
                dcc.Input(
                    id='search-destination',
                    type='text',
                    placeholder='Search restaurants, cuisine types, or locations...',
                    className='search-input',
                    debounce=False  # 即時搜尋
                )
            ], className='search-input-group', style={'position': 'relative', 'flex': '2'}),

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
            ], className='search-input-group', style={'flex': '1.3', 'minWidth': '200px', 'position': 'relative'}),

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
            ], className='search-input-group', style={'flex': '1.3', 'minWidth': '200px', 'position': 'relative'}),

            html.Button([
                html.I(className='fas fa-search', style={'marginRight': '8px'}),
                'Search'
            ], id='search-btn', className='search-btn', n_clicks=0),

            # Advanced filters toggle button
            html.Button([
                html.I(className='fas fa-sliders-h', style={'marginRight': '8px'}),
                'Filters'
            ], id='toggle-advanced-filters', className='btn-secondary', n_clicks=0, style={'marginLeft': '0.5rem'})
        ], className='search-container'),

        # Search suggestions dropdown (hidden by default)
        html.Div(id='search-suggestions', className='search-suggestions', style={'display': 'none'}),

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
                ], style={'marginBottom': '1.5rem'}),

                # Review count filter
                html.Div([
                    html.Label('Minimum Reviews', style={'color': '#deb522', 'fontWeight': 'bold', 'marginBottom': '0.5rem'}),
                    dcc.Slider(
                        id='review-count-filter',
                        min=0,
                        max=500,
                        step=10,
                        value=0,
                        marks={
                            0: '0',
                            100: '100',
                            200: '200',
                            300: '300',
                            500: '500+'
                        },
                        tooltip={'placement': 'bottom', 'always_visible': False}
                    )
                ], style={'marginBottom': '1.5rem'}),

                # Station/Area filter
                html.Div([
                    html.Label('Station/Area', style={'color': '#deb522', 'fontWeight': 'bold', 'marginBottom': '0.5rem'}),
                    dcc.Dropdown(
                        id='station-filter',
                        options=[{'label': station, 'value': station} for station in sorted(restaurants_df['Station'].dropna().unique())],
                        placeholder='All Stations',
                        multi=True,
                        className='search-input',
                        style={'backgroundColor': '#1a1a1a', 'border': '1px solid #333'}
                    )
                ], style={'marginBottom': '1.5rem'}),

                # Sort by options
                html.Div([
                    html.Label('Sort By', style={'color': '#deb522', 'fontWeight': 'bold', 'marginBottom': '0.5rem'}),
                    dcc.Dropdown(
                        id='sort-by-filter',
                        options=[
                            {'label': 'Highest Rating', 'value': 'rating_desc'},
                            {'label': 'Most Reviews', 'value': 'reviews_desc'},
                            {'label': 'Name (A-Z)', 'value': 'name_asc'},
                            {'label': 'Price (Low to High)', 'value': 'price_asc'},
                            {'label': 'Price (High to Low)', 'value': 'price_desc'}
                        ],
                        value='rating_desc',
                        className='search-input',
                        style={'backgroundColor': '#1a1a1a', 'border': '1px solid #333'}
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
        ], id='advanced-filters-panel', style={'display': 'none'}),

        # Active filter chips
        html.Div(id='active-filter-chips', style={'marginTop': '1rem'})
    ], style={'width': '100%'})

##########################
####   初始化應用程式   ####
##########################
app = Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    '/assets/voyage_styles.css'
],
           title='Voyage - Your Journey, Perfectly Planned', suppress_callback_exceptions=True)
server = app.server

# ===== 版面配置 =====
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Store(id='page-mode', data='login', storage_type='memory'),  # 'login' 或 'register'
    dcc.Store(id='current-page', data='overview', storage_type='memory'),  # 記錄當前頁面
    dcc.Store(id='menu-open', data=False, storage_type='memory'),  # 記錄選單開關狀態
    dcc.Store(id='view-mode', data='home', storage_type='memory'),  # 'home' 或 'restaurant-list'
    dcc.Store(id='navigation-trigger', storage_type='memory'),  # 導航觸發器
    dcc.Store(id='search-cuisine', storage_type='memory'),  # 選中的料理類型
    dcc.Store(id='search-rating', storage_type='memory'),  # 選中的評分範圍
    dcc.Store(id='active-dropdown', storage_type='memory', data=None),  # 當前打開的下拉菜單 ('cuisine', 'rating', or None)
    html.Div(id='page-content', style={'minHeight': '100vh'})
], style={'backgroundColor': '#1a1a1a', 'minHeight': '100vh'})

# 主應用布局（登入後顯示）
def create_main_layout():
    return html.Div([
        # ===== Global Header =====
        html.Div([
            html.Div([
                # Logo
                html.Div('Voyage', className='header-logo'),

                # Navigation
                html.Div([
                    html.Div('Destinations', className='nav-link', id='nav-destinations', n_clicks=0),
                    html.Div('Trip Planner', className='nav-link', id='nav-planner', n_clicks=0),
                    html.Div('Inspiration', className='nav-link', id='nav-inspiration', n_clicks=0)
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
                                html.I(className='fas fa-cog'),
                                html.Span('Settings')
                            ], className='dropdown-item', id='dropdown-settings', n_clicks=0),
                            html.Div([
                                html.I(className='fas fa-sign-out-alt'),
                                html.Span('Logout')
                            ], className='dropdown-item', id='menu-logout', n_clicks=0),
                        ], id='user-dropdown', className='user-dropdown')
                    ], style={'position': 'relative'})
                ], className='header-actions')
            ], className='header-content')
        ], className='global-header'),

        # Store for dropdown state
        dcc.Store(id='dropdown-open', data=False, storage_type='memory'),

        # ===== Hero Section =====
        html.Div([
            html.Img(src='/assets/Hazuki.jpg', className='hero-background'),
            html.Div(className='hero-overlay'),
            html.Div([
                html.H1('Your Journey, Perfectly Planned.', className='hero-title'),
                html.P('Discover and design your dream trip with personalized recommendations', className='hero-subtitle'),
                create_compound_search_bar()
            ], className='hero-content')
        ], className='hero-section'),

        # ===== Curated Content Section - Destinations You'll Love =====
        html.Div([
            html.Div([
                html.H2('Restaurants You\'ll Love', className='section-title'),
                html.A([
                    'View All',
                    html.I(className='fas fa-arrow-right')
                ], className='view-all-link', id='view-all-restaurants', n_clicks=0)
            ], className='section-header'),

            # Horizontal scrolling container
            html.Div([
                html.Div(id='destinations-card-container', className='card-row')
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

        # ===== Inspiration Content Section - Find Your Inspiration =====
        html.Div([
            html.Div([
                html.H2('Find Your Inspiration', className='section-title'),
                html.A([
                    'Explore More',
                    html.I(className='fas fa-arrow-right')
                ], className='view-all-link', id='view-all-inspiration', n_clicks=0)
            ], className='section-header'),

            # Article Grid
            html.Div(id='inspiration-grid-container', className='card-grid')
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
                            html.I(className='fas fa-cog'),
                            html.Span('Settings')
                        ], className='dropdown-item', id='dropdown-settings-list', n_clicks=0),
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

        # Stores for search results and pagination state
        dcc.Store(id='search-results-store', storage_type='memory'),
        dcc.Store(id='current-page-store', data=1, storage_type='memory'),
        dcc.Store(id='search-params-store', storage_type='memory')
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
     Input('view-mode', 'data')],
    prevent_initial_call=False
)
def display_page(pathname, session_data, current_mode, view_mode):
    """根據 session 狀態和 view_mode 顯示對應頁面"""
    # 清理過期 sessions
    clean_expired_sessions()

    # 檢查 session
    if session_data and 'session_id' in session_data:
        user_id = get_session(session_data['session_id'])
        if user_id:
            # 已登入，根據 view_mode 顯示不同頁面
            if view_mode == 'restaurant-list':
                return create_restaurant_list_page(), 'main'
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
    [Input('login-button', 'n_clicks')],
    [State('login-username', 'value'),
     State('login-password', 'value'),
     State('login-remember', 'value')],
    prevent_initial_call=True
)
def login(n_clicks, username, password, remember):
    """處理使用者登入"""
    if not n_clicks:
        raise PreventUpdate

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
    top_restaurants = get_random_top_restaurants(10)

    cards = []
    for _, restaurant in top_restaurants.iterrows():
        card = create_destination_card(restaurant)
        cards.append(card)

    return cards

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

# Populate Inspiration Grid
@app.callback(
    Output('inspiration-grid-container', 'children'),
    [Input('url', 'pathname')]
)
def populate_inspiration_grid(pathname):
    """填充靈感內容網格"""
    # Sample inspiration articles
    articles = [
        {'title': 'Top 10 Traditional Kyoto Restaurants', 'category': 'Food & Dining'},
        {'title': 'Hidden Gems in Kyoto: Local Favorites', 'category': 'Travel Guide'},
        {'title': 'Best Seasonal Dishes in Japan', 'category': 'Culinary'},
        {'title': 'How to Experience Authentic Japanese Cuisine', 'category': 'Tips & Tricks'},
        {'title': 'Weekend Getaway: Kyoto Food Tour', 'category': 'Itinerary'},
        {'title': 'Japanese Tea Ceremony: A Complete Guide', 'category': 'Culture'},
    ]

    cards = [dbc.Col(create_inspiration_card(article), width=12, md=6, lg=4)
             for article in articles]

    return dbc.Row(cards, style={'marginTop': '1rem'})

# Enhanced search function with advanced filters
def search_restaurants(keyword=None, cuisine=None, rating=None, price_range=None,
                      min_reviews=None, stations=None, sort_by='rating_desc'):
    """
    進階餐廳搜尋功能
    - keyword: 搜尋餐廳名稱（中英文）和料理類別
    - cuisine: 精確匹配料理類型
    - rating: 最低評分
    - price_range: 價格範圍 [min, max]
    - min_reviews: 最少評論數
    - stations: 車站列表（多選）
    - sort_by: 排序方式
    """
    filtered_df = restaurants_df.copy()

    # Keyword search: 搜尋 Name, JapaneseName, FirstCategory, SecondCategory, Station
    if keyword and keyword.strip():
        keyword_lower = keyword.lower().strip()
        # 支援模糊搜尋
        mask = (
            filtered_df['Name'].str.lower().str.contains(keyword_lower, na=False, regex=False) |
            filtered_df['JapaneseName'].str.contains(keyword, na=False, regex=False) |
            filtered_df['FirstCategory'].str.lower().str.contains(keyword_lower, na=False, regex=False) |
            filtered_df['SecondCategory'].str.lower().str.contains(keyword_lower, na=False, regex=False) |
            filtered_df['Station'].str.lower().str.contains(keyword_lower, na=False, regex=False)
        )
        filtered_df = filtered_df[mask]

    # Cuisine filter
    if cuisine:
        filtered_df = filtered_df[filtered_df['FirstCategory'] == cuisine]

    # Rating filter (区间筛选)
    if rating:
        if isinstance(rating, str) and '-' in rating:
            # 解析区间字符串 (例如 "4-5" -> 4.0 到 5.0)
            try:
                min_rating, max_rating = rating.split('-')
                min_rating = float(min_rating)
                max_rating = float(max_rating)
                filtered_df = filtered_df[
                    (filtered_df['TotalRating'] >= min_rating) &
                    (filtered_df['TotalRating'] < max_rating if max_rating < 5 else filtered_df['TotalRating'] <= max_rating)
                ]
            except (ValueError, AttributeError):
                pass  # 如果解析失败，跳过评分筛选
        else:
            # 向后兼容：如果是数字，使用大于等于逻辑
            try:
                rating_num = float(rating)
                filtered_df = filtered_df[filtered_df['TotalRating'] >= rating_num]
            except (ValueError, TypeError):
                pass

    # Price range filter (using average of lunch and dinner prices)
    if price_range and isinstance(price_range, (list, tuple)) and len(price_range) == 2:
        try:
            min_price, max_price = float(price_range[0]), float(price_range[1])
            # Calculate average price (handle NaN values)
            filtered_df['AvgPrice'] = filtered_df[['DinnerPrice', 'LunchPrice']].mean(axis=1)
            if max_price < 30000:
                filtered_df = filtered_df[
                    (filtered_df['AvgPrice'] >= min_price) &
                    (filtered_df['AvgPrice'] <= max_price)
                ]
            else:
                # Max price is 30000+, so only filter minimum
                filtered_df = filtered_df[filtered_df['AvgPrice'] >= min_price]
        except (ValueError, TypeError):
            pass  # Skip price filter if conversion fails

    # Review count filter
    if min_reviews:
        try:
            min_reviews_int = int(min_reviews)
            if min_reviews_int > 0:
                filtered_df = filtered_df[filtered_df['ReviewNum'] >= min_reviews_int]
        except (ValueError, TypeError):
            pass  # Skip review filter if conversion fails

    # Station filter (multi-select)
    if stations and len(stations) > 0:
        filtered_df = filtered_df[filtered_df['Station'].isin(stations)]

    # Sorting
    if sort_by == 'rating_desc':
        filtered_df = filtered_df.sort_values(by=['TotalRating', 'ReviewNum'], ascending=[False, False])
    elif sort_by == 'reviews_desc':
        filtered_df = filtered_df.sort_values(by=['ReviewNum', 'TotalRating'], ascending=[False, False])
    elif sort_by == 'name_asc':
        filtered_df = filtered_df.sort_values(by='Name', ascending=True)
    elif sort_by == 'price_asc':
        if 'AvgPrice' not in filtered_df.columns:
            filtered_df['AvgPrice'] = filtered_df[['DinnerPrice', 'LunchPrice']].mean(axis=1)
        filtered_df = filtered_df.sort_values(by='AvgPrice', ascending=True)
    elif sort_by == 'price_desc':
        if 'AvgPrice' not in filtered_df.columns:
            filtered_df['AvgPrice'] = filtered_df[['DinnerPrice', 'LunchPrice']].mean(axis=1)
        filtered_df = filtered_df.sort_values(by='AvgPrice', ascending=False)

    return filtered_df

# Get search suggestions based on keyword
def get_search_suggestions(keyword, max_results=8):
    """
    根據關鍵字生成搜尋建議
    返回餐廳名稱、料理類型、車站的匹配結果
    """
    if not keyword or len(keyword.strip()) < 2:
        return []

    keyword_lower = keyword.lower().strip()
    suggestions = []

    # Search in restaurant names
    name_matches = restaurants_df[
        restaurants_df['Name'].str.lower().str.contains(keyword_lower, na=False, regex=False)
    ]['Name'].head(3).tolist()

    for name in name_matches:
        suggestions.append({
            'type': 'restaurant',
            'value': name,
            'label': name,
            'icon': 'fa-utensils'
        })

    # Search in cuisine types (FirstCategory)
    cuisine_matches = restaurants_df[
        restaurants_df['FirstCategory'].str.lower().str.contains(keyword_lower, na=False, regex=False)
    ]['FirstCategory'].unique()[:3]

    for cuisine in cuisine_matches:
        suggestions.append({
            'type': 'cuisine',
            'value': cuisine,
            'label': f"{cuisine} (Cuisine)",
            'icon': 'fa-utensils'
        })

    # Search in stations
    station_matches = restaurants_df[
        restaurants_df['Station'].str.lower().str.contains(keyword_lower, na=False, regex=False)
    ]['Station'].unique()[:2]

    for station in station_matches:
        suggestions.append({
            'type': 'station',
            'value': station,
            'label': f"{station} (Station)",
            'icon': 'fa-map-marker-alt'
        })

    return suggestions[:max_results]

# ====== Search Enhancement Callbacks ======

# Show/hide search suggestions as user types
@app.callback(
    [Output('search-suggestions', 'children'),
     Output('search-suggestions', 'style')],
    [Input('search-destination', 'value')],
    prevent_initial_call=False
)
def update_search_suggestions(keyword):
    """即時顯示搜尋建議"""
    if not keyword or len(keyword.strip()) < 2:
        return [], {'display': 'none'}

    suggestions = get_search_suggestions(keyword)

    if not suggestions:
        return [], {'display': 'none'}

    # Create suggestion items
    suggestion_items = []
    for suggestion in suggestions:
        suggestion_items.append(
            html.Div([
                html.I(className=f'fas {suggestion["icon"]}', style={'marginRight': '12px', 'color': '#deb522', 'width': '20px'}),
                html.Span(suggestion['label'], style={'flex': '1'}),
                html.I(className='fas fa-arrow-right', style={'color': '#666', 'fontSize': '0.8rem'})
            ], className='suggestion-item', style={
                'padding': '12px 16px',
                'cursor': 'pointer',
                'display': 'flex',
                'alignItems': 'center',
                'borderBottom': '1px solid #333',
                'transition': 'background-color 0.2s',
                'color': '#ffffff'
            })
        )

    return suggestion_items, {
        'display': 'block',
        'position': 'absolute',
        'top': '100%',
        'left': '0',
        'right': '0',
        'backgroundColor': '#1a1a1a',
        'border': '1px solid #deb522',
        'borderTop': 'none',
        'borderRadius': '0 0 8px 8px',
        'maxHeight': '400px',
        'overflowY': 'auto',
        'zIndex': '1000',
        'marginTop': '-1px'
    }

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
     Output('review-count-filter', 'value'),
     Output('station-filter', 'value'),
     Output('sort-by-filter', 'value'),
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
            '', None, None, [0, 30000], 0, None, 'rating_desc',
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

# Display active filter chips
@app.callback(
    Output('active-filter-chips', 'children'),
    [Input('search-destination', 'value'),
     Input('search-cuisine', 'data'),
     Input('search-rating', 'data'),
     Input('price-range-filter', 'value'),
     Input('review-count-filter', 'value'),
     Input('station-filter', 'value')]
)
def display_active_filters(keyword, cuisine, rating, price_range, min_reviews, stations):
    """顯示當前激活的篩選條件標籤"""
    chips = []

    if keyword:
        chips.append(
            html.Span([
                html.I(className='fas fa-search', style={'marginRight': '6px'}),
                f'"{keyword}"',
                html.I(className='fas fa-times', style={'marginLeft': '8px', 'cursor': 'pointer'})
            ], className='filter-chip', style={
                'display': 'inline-flex',
                'alignItems': 'center',
                'backgroundColor': '#deb522',
                'color': '#000',
                'padding': '6px 12px',
                'borderRadius': '20px',
                'fontSize': '0.85rem',
                'marginRight': '8px',
                'marginBottom': '8px',
                'fontWeight': '500'
            })
        )

    if cuisine:
        chips.append(
            html.Span([
                html.I(className='fas fa-utensils', style={'marginRight': '6px'}),
                cuisine
            ], className='filter-chip', style={
                'display': 'inline-flex',
                'alignItems': 'center',
                'backgroundColor': '#333',
                'color': '#deb522',
                'padding': '6px 12px',
                'borderRadius': '20px',
                'fontSize': '0.85rem',
                'marginRight': '8px',
                'marginBottom': '8px',
                'border': '1px solid #deb522'
            })
        )

    if rating:
        chips.append(
            html.Span([
                html.I(className='fas fa-star', style={'marginRight': '6px'}),
                f'{rating}+ Stars'
            ], className='filter-chip', style={
                'display': 'inline-flex',
                'alignItems': 'center',
                'backgroundColor': '#333',
                'color': '#deb522',
                'padding': '6px 12px',
                'borderRadius': '20px',
                'fontSize': '0.85rem',
                'marginRight': '8px',
                'marginBottom': '8px',
                'border': '1px solid #deb522'
            })
        )

    if price_range and isinstance(price_range, list) and len(price_range) == 2:
        if price_range[0] > 0 or price_range[1] < 30000:
            chips.append(
                html.Span([
                    html.I(className='fas fa-yen-sign', style={'marginRight': '6px'}),
                    f'¥{int(price_range[0]):,} - ¥{int(price_range[1]):,}'
                ], className='filter-chip', style={
                    'display': 'inline-flex',
                    'alignItems': 'center',
                    'backgroundColor': '#333',
                    'color': '#deb522',
                    'padding': '6px 12px',
                    'borderRadius': '20px',
                    'fontSize': '0.85rem',
                    'marginRight': '8px',
                    'marginBottom': '8px',
                    'border': '1px solid #deb522'
                })
            )

    if min_reviews and int(min_reviews) > 0:
        chips.append(
            html.Span([
                html.I(className='fas fa-comment', style={'marginRight': '6px'}),
                f'{int(min_reviews)}+ Reviews'
            ], className='filter-chip', style={
                'display': 'inline-flex',
                'alignItems': 'center',
                'backgroundColor': '#333',
                'color': '#deb522',
                'padding': '6px 12px',
                'borderRadius': '20px',
                'fontSize': '0.85rem',
                'marginRight': '8px',
                'marginBottom': '8px',
                'border': '1px solid #deb522'
            })
        )

    if stations:
        for station in stations:
            chips.append(
                html.Span([
                    html.I(className='fas fa-map-marker-alt', style={'marginRight': '6px'}),
                    station
                ], className='filter-chip', style={
                    'display': 'inline-flex',
                    'alignItems': 'center',
                    'backgroundColor': '#333',
                    'color': '#deb522',
                    'padding': '6px 12px',
                    'borderRadius': '20px',
                    'fontSize': '0.85rem',
                    'marginRight': '8px',
                    'marginBottom': '8px',
                    'border': '1px solid #deb522'
                })
            )

    if chips:
        return html.Div(chips, style={'display': 'flex', 'flexWrap': 'wrap', 'alignItems': 'center'})
    return []

# Handle Search Button with advanced filters (home page preview)
# 自动搜索：当选择料理类型或评分时自动触发搜索
@app.callback(
    Output('destinations-card-container', 'children', allow_duplicate=True),
    [Input('search-btn', 'n_clicks'),
     Input('search-cuisine', 'data'),
     Input('search-rating', 'data')],
    [State('search-destination', 'value'),
     State('price-range-filter', 'value'),
     State('review-count-filter', 'value'),
     State('station-filter', 'value'),
     State('sort-by-filter', 'value')],
    prevent_initial_call=True
)
def handle_search(n_clicks, cuisine, rating, destination, price_range, min_reviews, stations, sort_by):
    """處理搜尋功能（首頁預覽）- 支援進階篩選和自動搜索"""
    # 不需要检查 n_clicks，因为 dropdown 改变也会触发搜索

    # Ensure default values for None parameters
    if price_range is None:
        price_range = [0, 30000]
    if min_reviews is None:
        min_reviews = 0
    if stations is None:
        stations = []
    if sort_by is None:
        sort_by = 'rating_desc'

    # Use enhanced search function with all filters
    filtered_df = search_restaurants(
        keyword=destination,
        cuisine=cuisine,
        rating=rating,
        price_range=price_range,
        min_reviews=min_reviews,
        stations=stations,
        sort_by=sort_by
    )

    # Get top results for preview
    if len(filtered_df) > 0:
        # Show top 10 for preview
        preview_df = filtered_df.head(10)
        cards = [create_destination_card(row) for _, row in preview_df.iterrows()]
        return cards
    else:
        return [html.Div([
            html.I(className='fas fa-search', style={'fontSize': '3rem', 'color': '#deb522', 'marginBottom': '1rem'}),
            html.H3('No restaurants found', style={'color': '#ffffff'}),
            html.P('Try adjusting your search criteria', style={'color': '#888888'})
        ], style={'textAlign': 'center', 'padding': '4rem', 'width': '100%'})]

# ====== Restaurant List Page Callbacks ======

# Handle search in restaurant list page with advanced filters
# 自动搜索：当选择料理类型或评分时自动触发搜索
@app.callback(
    [Output('search-results-store', 'data'),
     Output('current-page-store', 'data'),
     Output('search-params-store', 'data')],
    [Input('search-btn', 'n_clicks'),
     Input('search-cuisine', 'data'),
     Input('search-rating', 'data'),
     Input('sort-by-filter', 'value')],  # Also trigger on sort change
    [State('search-destination', 'value'),
     State('price-range-filter', 'value'),
     State('review-count-filter', 'value'),
     State('station-filter', 'value'),
     State('view-mode', 'data')],
    prevent_initial_call=True
)
def handle_restaurant_list_search(n_clicks, cuisine, rating, sort_by, destination, price_range, min_reviews, stations, view_mode):
    """處理餐廳列表頁的搜尋功能 - 支援進階篩選、排序和自動搜索"""
    if view_mode != 'restaurant-list':
        raise PreventUpdate

    # Ensure default values for None parameters
    if price_range is None:
        price_range = [0, 30000]
    if min_reviews is None:
        min_reviews = 0
    if stations is None:
        stations = []
    if sort_by is None:
        sort_by = 'rating_desc'

    # Use enhanced search function with all filters
    filtered_df = search_restaurants(
        keyword=destination,
        cuisine=cuisine,
        rating=rating,
        price_range=price_range,
        min_reviews=min_reviews,
        stations=stations,
        sort_by=sort_by
    )

    # Store search results and parameters
    search_results = filtered_df.to_dict('records') if len(filtered_df) > 0 else []
    search_params = {
        'destination': destination,
        'cuisine': cuisine,
        'rating': rating,
        'price_range': price_range,
        'min_reviews': min_reviews,
        'stations': stations,
        'sort_by': sort_by
    }

    return search_results, 1, search_params  # Reset to page 1

# Initialize restaurant list page with all restaurants
@app.callback(
    [Output('search-results-store', 'data', allow_duplicate=True),
     Output('current-page-store', 'data', allow_duplicate=True)],
    [Input('view-mode', 'data')],
    prevent_initial_call=True
)
def initialize_restaurant_list(view_mode):
    """初始化餐廳列表頁（顯示所有餐廳）"""
    if view_mode == 'restaurant-list':
        # Show all restaurants sorted by rating
        all_restaurants = restaurants_df.sort_values(
            by=['TotalRating', 'ReviewNum'],
            ascending=[False, False]
        ).to_dict('records')
        return all_restaurants, 1
    raise PreventUpdate

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
        card = html.Div([
            html.Img(
                src='/assets/Hazuki.jpg',
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
    button_data = eval(button_id)  # Convert string to dict
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

if __name__ == '__main__':
    app.run(debug=True)
