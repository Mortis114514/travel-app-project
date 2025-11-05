# Import 所有相關套件
from dash import Dash, html, dcc, Input, State, Output, dash_table, no_update, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import dash_leaflet as dl
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import uuid
import random
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
# 加載欲分析的資料集# 旅遊資訊
restaurants_df = pd.read_csv('./data/Kyoto_Restaurant_Info_Full.csv')  # 餐廳資訊

# 切換頁面（如有需要可以自行增加）
def load_data(tab):
    if tab in ('travel', 'planner'):
        return df_merged
def create_sort_controls():
    """創建排序和篩選控制選項"""
    return html.Div([
        # Price Range Filter
        html.Div([
            html.Label('Price Range:', style={
                'color': '#ffffff',
                'marginRight': '10px',
                'fontSize': '0.95rem',
                'fontWeight': '500'
            }),
            dcc.Dropdown(
                id='price-filter-dropdown',
                options=[
                    {'label': '💎 All Prices', 'value': 'all'},
                    {'label': '💎 頂級 (Top Tier)', 'value': '頂級'},
                    {'label': '💰 高價位 (High)', 'value': '高價位'},
                    {'label': '💵 中價位 (Medium)', 'value': '中價位'},
                    {'label': '💳 平價 (Budget)', 'value': '平價'},
                    {'label': '❓ 未知 (Unknown)', 'value': '未知'},
                ],
                value='all',  # Default: show all
                clearable=False,
                style={
                    'minWidth': '200px',
                    'backgroundColor': '#2a2a2a',
                    'color': '#ffffff'
                }
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'marginRight': '20px'
        }),
        
        # Sort By Dropdown
        html.Div([
            html.Label('Sort by:', style={
                'color': '#ffffff',
                'marginRight': '10px',
                'fontSize': '0.95rem',
                'fontWeight': '500'
            }),
            dcc.Dropdown(
                id='sort-by-dropdown',
                options=[
                    {'label': '💰 Price: High to Low', 'value': 'price_desc'},
                    {'label': '💰 Price: Low to High', 'value': 'price_asc'},
                    {'label': '⭐ Rating: High to Low', 'value': 'rating_desc'},
                    {'label': '⭐ Rating: Low to High', 'value': 'rating_asc'},
                    {'label': '🔤 Name: A to Z', 'value': 'name_asc'},
                ],
                value='rating_desc',  # Default sorting
                clearable=False,
                style={
                    'minWidth': '220px',
                    'backgroundColor': '#2a2a2a',
                    'color': '#ffffff'
                }
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center'
        })
    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'flexWrap': 'wrap',
        'gap': '10px'
    })

# 隨機選擇4-5星餐廳
def get_random_top_restaurants(n=5):
    """從4-5星餐廳中隨機選擇n個餐廳"""
    top_restaurants = restaurants_df[restaurants_df['Rating_Category'] == '4~5 星餐廳'].copy()
    if len(top_restaurants) >= n:
        return top_restaurants.sample(n=n)
    else:
        return top_restaurants

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
    """創建複合式搜尋欄"""
    return html.Div([
        html.Div([
            html.I(className='fas fa-search'),
            dcc.Input(
                id='search-destination',
                type='text',
                placeholder='Where do you want to go?',
                className='search-input'
            )
        ], className='search-input-group'),

        html.Div([
            html.I(className='fas fa-utensils'),
            dcc.Dropdown(
                id='search-cuisine',
                options=[{'label': cat, 'value': cat} for cat in restaurants_df['FirstCategory'].dropna().unique()],
                placeholder='Cuisine Type',
                className='search-input',
                style={'border': 'none', 'background': 'transparent'}
            )
        ], className='search-input-group'),

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
                style={'border': 'none', 'background': 'transparent'}
            )
        ], className='search-input-group'),

        html.Button([
            html.I(className='fas fa-search', style={'marginRight': '8px'}),
            'Search'
        ], id='search-btn', className='search-btn', n_clicks=0)
    ], className='search-container')

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
                html.H2('Restaurants You\'ll Love', className='section-title'),
                html.Div([
                    create_sort_controls(),  # Add sorting and filter controls
                    html.A([
                        'View All',
                        html.I(className='fas fa-arrow-right')
                    ], className='view-all-link', id='view-all-restaurants', n_clicks=0)
                ], style={'display': 'flex', 'alignItems': 'center', 'gap': '20px', 'flexWrap': 'wrap'})
            ], className='section-header', style={'alignItems': 'flex-start'}),

            # Horizontal scrolling container
            html.Div([
                html.Div(id='destinations-card-container', className='card-row')
            ], className='card-scroll-container')
        ], className='content-section'),

    ], style={'backgroundColor': '#0a0a0a', 'minHeight': '100vh'})

# ====== 認證相關 Callbacks ======

# 頁面路由控制
@app.callback(
    [Output('page-content', 'children'),
     Output('page-mode', 'data')],
    [Input('url', 'pathname'),
     Input('session-store', 'data'),
     Input('page-mode', 'data')],
    prevent_initial_call=False
)
def display_page(pathname, session_data, current_mode):
    """根據 session 狀態顯示登入頁或主頁面"""
    # 清理過期 sessions
    clean_expired_sessions()

    # 檢查 session
    if session_data and 'session_id' in session_data:
        user_id = get_session(session_data['session_id'])
        if user_id:
            # 已登入，顯示主應用
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
    [Input('url', 'pathname'),
     Input('price-filter-dropdown', 'value'),
     Input('sort-by-dropdown', 'value')],
    prevent_initial_call=False
)
def populate_destinations_cards(pathname, price_filter, sort_by):
    """填充餐廳卡片（橫向滾動）with filtering and sorting"""
    
    # Define price category order (most expensive to cheapest)
    price_order = {
        '頂級': 5,
        '高價位': 4,
        '中價位': 3,
        '平價': 2,
        '未知': 1
    }
    
    # Start with all restaurants or filter for top ones
    top_restaurants = restaurants_df.copy()
    
    # Add numeric price column for sorting
    if 'Price_Category' in top_restaurants.columns:
        top_restaurants['Price_Order'] = top_restaurants['Price_Category'].map(price_order).fillna(0)
    
    # STEP 1: Filter by Price Range
    if price_filter != 'all':
        if 'Price_Category' in top_restaurants.columns:
            top_restaurants = top_restaurants[top_restaurants['Price_Category'] == price_filter]
    
    # STEP 2: Apply sorting based on dropdown selection
    if sort_by == 'price_desc':
        # Sort by Price_Category (most expensive first: 頂級 -> 平價)
        if 'Price_Order' in top_restaurants.columns:
            top_restaurants = top_restaurants.sort_values('Price_Order', ascending=False)
        else:
            top_restaurants = top_restaurants.sort_values('TotalRating', ascending=False)
            
    elif sort_by == 'price_asc':
        # Sort by Price_Category (cheapest first: 平價 -> 頂級)
        if 'Price_Order' in top_restaurants.columns:
            top_restaurants = top_restaurants.sort_values('Price_Order', ascending=True)
        else:
            top_restaurants = top_restaurants.sort_values('TotalRating', ascending=True)
            
    elif sort_by == 'rating_desc':
        top_restaurants = top_restaurants.sort_values('TotalRating', ascending=False)
        
    elif sort_by == 'rating_asc':
        top_restaurants = top_restaurants.sort_values('TotalRating', ascending=True)
        
    elif sort_by == 'name_asc':
        top_restaurants = top_restaurants.sort_values('Name', ascending=True)
    
    # Limit to top 20 results for performance
    top_restaurants = top_restaurants.head(20)
    
    # Create cards
    cards = []
    for _, restaurant in top_restaurants.iterrows():
        card = create_destination_card(restaurant)
        cards.append(card)
    
    # If no restaurants found
    if len(cards) == 0:
        return [html.Div([
            html.I(className='fas fa-utensils', style={
                'fontSize': '3rem', 
                'color': '#deb522', 
                'marginBottom': '1rem'
            }),
            html.H3('No restaurants found', style={'color': '#ffffff'}),
            html.P('Try adjusting your filters', style={'color': '#888888'})
        ], style={'textAlign': 'center', 'padding': '4rem', 'width': '100%'})]
    
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

        content = html.Div(cards + [create_add_new_card()], className='card-row')
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

# Handle Search Button
@app.callback(
    Output('destinations-card-container', 'children', allow_duplicate=True),
    [Input('search-btn', 'n_clicks')],
    [State('search-destination', 'value'),
     State('search-cuisine', 'value'),
     State('search-rating', 'value'),
     State('price-filter-dropdown', 'value'),
     State('sort-by-dropdown', 'value')],
    prevent_initial_call=True
)
def handle_search(n_clicks, destination, cuisine, rating, price_filter, sort_by):
    """處理搜尋功能 with filters"""
    if not n_clicks:
        raise PreventUpdate

    # Define price category order
    price_order = {
        '頂級': 5,
        '高價位': 4,
        '中價位': 3,
        '平價': 2,
        '未知': 1
    }

    # Filter restaurants based on search criteria
    filtered_df = restaurants_df.copy()
    
    # Add numeric price column
    if 'Price_Category' in filtered_df.columns:
        filtered_df['Price_Order'] = filtered_df['Price_Category'].map(price_order).fillna(0)

    if destination:
        filtered_df = filtered_df[
            filtered_df['Name'].str.contains(destination, case=False, na=False) |
            filtered_df['Station'].str.contains(destination, case=False, na=False)
        ]

    if cuisine:
        filtered_df = filtered_df[filtered_df['FirstCategory'] == cuisine]

    if rating:
        filtered_df = filtered_df[filtered_df['TotalRating'] >= rating]
    
    # Apply price filter
    if price_filter != 'all':
        if 'Price_Category' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Price_Category'] == price_filter]

    # Apply sorting
    if sort_by == 'price_desc':
        if 'Price_Order' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('Price_Order', ascending=False)
    elif sort_by == 'price_asc':
        if 'Price_Order' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('Price_Order', ascending=True)
    elif sort_by == 'rating_desc':
        filtered_df = filtered_df.sort_values('TotalRating', ascending=False)
    elif sort_by == 'rating_asc':
        filtered_df = filtered_df.sort_values('TotalRating', ascending=True)
    elif sort_by == 'name_asc':
        filtered_df = filtered_df.sort_values('Name', ascending=True)

    # Get top results (top 20)
    if len(filtered_df) > 0:
        filtered_df = filtered_df.head(20)
        cards = [create_destination_card(row) for _, row in filtered_df.iterrows()]
        return cards
    else:
        return [html.Div([
            html.I(className='fas fa-search', style={'fontSize': '3rem', 'color': '#deb522', 'marginBottom': '1rem'}),
            html.H3('No restaurants found', style={'color': '#ffffff'}),
            html.P('Try adjusting your search criteria', style={'color': '#888888'})
        ], style={'textAlign': 'center', 'padding': '4rem', 'width': '100%'})]

if __name__ == '__main__':
    app.run(debug=True)
