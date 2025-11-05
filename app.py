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
# 加載欲分析的資料集
travel_df = pd.read_csv('./data/Travel_dataset.csv')  # 旅遊資訊
country_info_df = pd.read_csv('./data/country_info.csv')  # 國家資訊
attractions_df = pd.read_csv('./data/Attractions.csv')  # 景點資訊
restaurants_df = pd.read_csv('./data/Kyoto_Restaurant_Info_Rated.csv')  # 餐廳資訊

# 進行資料前處理
travel_df = travel_data_clean(travel_df)
country_info_df = countryinfo_data_clean(country_info_df)

# 合併 travel_df 和 country_info_df，方便後續分析
df_merged = data_merge(travel_df, country_info_df)

# 呼叫 ./utils/const.py 中的 get_constants() 函式（畫面上方四格統計）
num_of_country, num_of_traveler, num_of_nationality, avg_days = get_constants(travel_df)

# 獲取國家名稱列表（景點頁使用）
country_list = list(attractions_df['country'].unique())

# 設定 Overview 頁面預設值
DEFAULTS = get_dashboard_default_values(df_merged)

# 切換頁面（如有需要可以自行增加）
def load_data(tab):
    if tab in ('travel', 'planner'):
        return df_merged

# 隨機選擇5個4-5星餐廳
def get_random_top_restaurants(n=5):
    """從4-5星餐廳中隨機選擇n個餐廳"""
    top_restaurants = restaurants_df[restaurants_df['Rating_Category'] == '4~5 星餐廳'].copy()
    if len(top_restaurants) >= n:
        return top_restaurants.sample(n=n)
    else:
        return top_restaurants

##########################
####   初始化應用程式   ####
##########################
app = Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    '/assets/gear_menu.css'
],
           title='Travel Data Analysis Dashboard', suppress_callback_exceptions=True)
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
    return dbc.Container([
        # 齒輪選單按鈕
        html.Div([
            html.Div([
                html.Div([
                    html.Div(className='hamburger-line'),
                    html.Div(className='hamburger-line'),
                ], className='hamburger-lines')
            ], id='gear-button', className='gear-button', n_clicks=0),

            # 下拉選單
            html.Div([
                html.Div([
                    html.I(className='fas fa-chart-line'),
                    html.Span('Overview')
                ], id='menu-overview', className='menu-item', n_clicks=0),

                html.Div([
                    html.I(className='fas fa-map-marked-alt'),
                    html.Span('Trip Planner')
                ], id='menu-planner', className='menu-item', n_clicks=0),

                html.Div([
                    html.I(className='fas fa-map-pin'),
                    html.Span('Attractions')
                ], id='menu-attractions', className='menu-item', n_clicks=0),

                html.Div(className='menu-divider'),

                html.Div([
                    html.I(className='fas fa-sign-out-alt'),
                    html.Span('登出')
                ], id='menu-logout', className='menu-item logout-item', n_clicks=0),
            ], id='menu-dropdown', className='menu-dropdown')
        ], className='gear-menu-container'),

        # 頂部 Logo
        dbc.Row([
            dbc.Col(html.Img(src="./assets/logo.png", height=100), width=12, style={'marginTop': '15px', 'textAlign': 'center'}),
        ]),

        # 四格統計
        dbc.Row([
            dbc.Col(generate_stats_card("Country", num_of_country, "./assets/earth.svg"), width=3),
            dbc.Col(generate_stats_card("Traveler", num_of_traveler, "./assets/user.svg"), width=3),
            dbc.Col(generate_stats_card("Nationality", num_of_nationality, "./assets/earth.svg"), width=3),
            dbc.Col(generate_stats_card("Average Days", avg_days, "./assets/calendar.svg"), width=3),
        ], style={'marginBlock': '10px'}),

        # 頁面主要內容的放置區(容器)
        html.Div(id='graph-content'),

        # 熱門餐廳區域
        html.Div([
            html.H2("🍣 熱門餐廳", style={
                'color': '#deb522',
                'textAlign': 'center',
                'marginTop': '30px',
                'marginBottom': '20px',
                'fontWeight': 'bold'
            }),

            # 餐廳卡片容器
            html.Div(id='popular-restaurants-container')
        ], style={'marginBottom': '30px'})
    ], style={'padding': '0px'})

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

# ====== 齒輪選單相關 Callbacks ======

# 切換選單開關狀態
@app.callback(
    Output('menu-open', 'data'),
    [Input('gear-button', 'n_clicks')],
    [State('menu-open', 'data')],
    prevent_initial_call=True
)
def toggle_menu(n_clicks, is_open):
    """切換選單的開關狀態"""
    return not is_open

# 更新選單和齒輪的顯示樣式
@app.callback(
    [Output('menu-dropdown', 'className'),
     Output('gear-button', 'className')],
    [Input('menu-open', 'data')]
)
def update_menu_display(is_open):
    """根據開關狀態更新選單和齒輪的樣式"""
    if is_open:
        return 'menu-dropdown show', 'gear-button active'
    return 'menu-dropdown', 'gear-button'

# 處理選單項目點擊 - 切換頁面
@app.callback(
    [Output('current-page', 'data'),
     Output('menu-open', 'data', allow_duplicate=True)],
    [Input('menu-overview', 'n_clicks'),
     Input('menu-planner', 'n_clicks'),
     Input('menu-attractions', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_page(overview_clicks, planner_clicks, attractions_clicks):
    """根據點擊的選單項目切換頁面"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # 根據點擊的按鈕決定顯示哪個頁面
    page_map = {
        'menu-overview': 'overview',
        'menu-planner': 'planner',
        'menu-attractions': 'attractions'
    }

    return page_map.get(button_id, 'overview'), False  # 切換頁面後關閉選單

# 處理登出按鈕
@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    [Input('menu-logout', 'n_clicks')],
    [State('session-store', 'data')],
    prevent_initial_call=True
)
def logout_from_menu(n_clicks, session_data):
    """從選單登出"""
    if not n_clicks:
        raise PreventUpdate

    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])

    return None

# 更新選單項目的 active 狀態
@app.callback(
    [Output('menu-overview', 'className'),
     Output('menu-planner', 'className'),
     Output('menu-attractions', 'className')],
    [Input('current-page', 'data')]
)
def update_menu_active_state(current_page):
    """根據當前頁面更新選單項目的 active 狀態"""
    base_class = 'menu-item'
    active_class = 'menu-item active'

    return (
        active_class if current_page == 'overview' else base_class,
        active_class if current_page == 'planner' else base_class,
        active_class if current_page == 'attractions' else base_class
    )

# ====== 頁面切換內容 ======
@app.callback(
    Output('graph-content', 'children'),
    [Input('current-page', 'data')]
)
def render_tab_content(tab):
    if tab == 'overview':
        # 建立地理選項（洲 + 國家）
        geo_options = [{'label': i, 'value': i}
                       for i in pd.concat([df_merged['Continent'], df_merged['Destination']]).dropna().unique()]

        return html.Div([
            # 第一排：長條 + 圓餅
            dbc.Row([
                dbc.Col([
                    html.H3("各大洲或各國不同月份遊客人數", style={'color': '#deb522', 'margin-top': '5px'}),
                    dcc.Dropdown(
                        id='dropdown-bar-1',
                        options=geo_options,
                        value=DEFAULTS["bar1_geo"],
                        placeholder='Select a continent or country',
                        style={'width': '90%','margin-top': '10px','margin-bottom': '10px'}
                    )
                ]),
                dbc.Col([
                    html.H3("各大洲或各國的遊客屬性、住宿及交通類型", style={'color': '#deb522', 'margin-top': '5px'}),
                    dcc.Dropdown(
                        id='dropdown-pie-1',
                        options=geo_options,
                        value=DEFAULTS["pie1_geo"],
                        placeholder='Select a continent or country',
                        style={'width': '50%','margin':'5px 0','display': 'inline-block'}
                    ),
                    dcc.Dropdown(
                        id='dropdown-pie-2',
                        options=[{'label': i, 'value': i}
                                 for i in ['Traveler nationality','Age group','Traveler gender','Accommodation type','Transportation type']],
                        value=DEFAULTS["pie2_field"],
                        placeholder='Select a value',
                        style={'width': '50%','margin':'5px 0','display': 'inline-block'}
                    )
                ]),
            ]),
            dbc.Row([
                dbc.Col([dcc.Loading([html.Div(id='tabs-content-1')], type='default', color='#deb522')]),
                dbc.Col([dcc.Loading([html.Div(id='tabs-content-2')], type='default', color='#deb522')]),
            ]),
            # 第二排：地圖 + 箱型圖
            dbc.Row([
                dbc.Col([
                    html.H3("各大洲或各國安全係數及消費水平", style={'color': '#deb522', 'margin-top': '5px'}),
                    dcc.Dropdown(
                        id='dropdown-map-1',
                        options=[{'label': 'All', 'value': None}]
                                + [{'label': i, 'value': i} for i in df_merged['Continent'].dropna().unique()],
                        value=DEFAULTS["map1_geo"],
                        placeholder='Select a continent',
                        style={'width': '50%','margin':'5px 0','display': 'inline-block'}
                    ),
                    dcc.Dropdown(
                        id='dropdown-map-2',
                        options=[{'label': i, 'value': i} for i in ['Safety Index','Crime_index','CPI','PCE','Exchange_rate']],
                        value=DEFAULTS["map2_metric"],
                        placeholder='Select a value',
                        style={'width': '50%','margin':'5px 0','display': 'inline-block'}
                    )
                ]),
                dbc.Col([
                    html.H3("各大洲或各國家住宿及交通成本", style={'color': '#deb522', 'margin-top': '5px'}),
                    dcc.Dropdown(
                        id='dropdown-box-1',
                        options=[{'label': i, 'value': i}
                                 for i in pd.concat([df_merged['Continent'], df_merged['Destination']]).dropna().unique()],
                        value=DEFAULTS["box1_geo"],
                        placeholder='Select a continent or country',
                        style={'width': '50%','margin':'5px 0','display': 'inline-block'}
                    ),
                    dcc.Dropdown(
                        id='dropdown-box-2',
                        options=[{'label': i, 'value': i} for i in ['Accommodation cost','Transportation cost']],
                        value=DEFAULTS["box2_metric"],
                        placeholder='Select a value',
                        style={'width': '50%','margin':'5px 0','display': 'inline-block'}
                    )
                ]),
            ]),
            dbc.Row([
                dbc.Col([dcc.Loading([html.Div(id='tabs-content-3')], type='default', color='#deb522')]),
                dbc.Col([dcc.Loading([html.Div(id='tabs-content-4')], type='default', color='#deb522')]),
            ]),
        ])

    elif tab == 'planner':
        # 從資料集中取得所有住宿類型
        accommodation_types = sorted(travel_df['Accommodation type'].dropna().unique().tolist())

        # 從 country_info_df 中取出所有「Travel Alert」欄位的值
        alerts_from_country = country_info_df['Travel Alert'].dropna().astype(str).str.strip().tolist() \
                              if 'Travel Alert' in country_info_df.columns else []
        # 從 df_merged 中取出所有「Travel Alert」欄位的值
        alerts_from_merged = df_merged['Travel Alert'].dropna().astype(str).str.strip().tolist() \
                             if 'Travel Alert' in df_merged.columns else []
        # 合併兩者並去除重複值
        seen_alerts = sorted(set(alerts_from_country) | set(alerts_from_merged))
        # 根據等級排序所有警示顏色
        sorted_alerts = sorted(seen_alerts, key=get_alert_rank)
        # 轉換成 Dash 下拉選單需要的格式
        color_options = []
        for alert in sorted_alerts:
            color_options.append({
                'label': alert,   # 顯示在畫面上的文字
                'value': alert    # 實際回傳的值
            })  
        # 預設選項為最安全的顏色
        if len(color_options) > 0:
            default_alert = color_options[0]['value']
        else:
            default_alert = None

        # 回傳 Trip Planner 頁面的版面配置
        return html.Div([
            dcc.Store(id='planner-selected-countries', data=[]),  # 只用來存「前五名」供比較圖表使用

            html.H3("Trip Planner：用預算、安全與住宿偏好找旅遊國家", style={'color': '#deb522', 'margin-top': '5px'}),

            # 篩選列 1：住宿費用 & 住宿類型
            dbc.Row([
                dbc.Col([
                    html.Label("Accommodation cost（min）", style={'color': '#deb522'}),
                    dcc.Input(id='planner-cost-min', type='number', placeholder='min',
                              style={'width': '100%','backgroundColor': 'black','color': '#deb522','border': '1px solid #deb522'})
                ], width=3),
                dbc.Col([
                    html.Label("Accommodation cost（max）", style={'color': '#deb522'}),
                    dcc.Input(id='planner-cost-max', type='number', placeholder='max',
                              style={'width': '100%','backgroundColor': 'black','color': '#deb522','border': '1px solid #deb522'})
                ], width=3),
                dbc.Col([
                    html.Label("Accommodation type（multi）", style={'color': '#deb522'}),
                    dcc.Dropdown(id='planner-acc-types',
                                 options=[{'label': t, 'value': t} for t in accommodation_types],
                                 value=[], multi=True, style={'backgroundColor': '#deb522','color': 'black'})
                ], width=6),
            ], style={'marginTop': '8px', 'marginBottom': '12px'}),

            # 篩選列 2：安全顏色門檻、免簽
            dbc.Row([
                dbc.Col([
                    html.Label("可接受的最高危險顏色（含以下等級）", style={'color': '#deb522'}),
                    dcc.Dropdown(
                        id='planner-alert-max', options=color_options, value=default_alert, clearable=False,
                        style={'backgroundColor': '#deb522', 'color': 'black'}
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Visa", style={'color': '#deb522'}),
                    dcc.Checklist(
                        id='planner-visa-only',
                        options=[{'label': ' 只顯示免簽', 'value': 'exempt'}],
                        value=[], inputStyle={'marginRight': '6px'}, labelStyle={'color': '#deb522'}
                    )
                ], width=6),
            ], style={'marginBottom': '12px'}),

            # 權重設定
            dbc.Row([
                dbc.Col([
                    html.Label("Weights（0–10）：Safety / Cost", style={'color': '#deb522'}),
                    html.Div([
                        dcc.Slider(id='w-safety', min=0, max=10, step=1, value=7, marks=None, tooltip={'always_visible': True}),
                        dcc.Slider(id='w-cost', min=0, max=10, step=1, value=8, marks=None, tooltip={'always_visible': True}),
                    ], style={'paddingTop': '10px'})
                ], width=12),
            ], style={'marginBottom': '8px'}),

            # 顯示推薦國家表格
            dcc.Loading([html.Div(id='planner-table-container')], type='default', color='#deb522'),

            html.Hr(style={'borderColor': '#deb522'}),

            # 比較圖表
            html.H4("建議國家比較", style={'color': '#deb522', 'marginTop': '10px'}),
            dbc.Row([
                dbc.Col([dcc.Loading(html.Div(id='planner-compare-radar'), type='default', color='#deb522')], width=6),
                dbc.Col([dcc.Loading(html.Div(id='planner-compare-bar'), type='default', color='#deb522')], width=6),
            ], style={'marginBottom': '12px'}),
            dbc.Row([
                dbc.Col([dcc.Loading(html.Div(id='planner-compare-line'), type='default', color='#deb522')], width=12),
            ], style={'marginBottom': '12px'}),
        ])

    elif tab == 'attractions':
        return html.Div([
            # 選擇欲顯示Attrations列表與地圖的國家(下拉式選單)
            dcc.Dropdown(
                options=[{'label': country, 'value': country} for country in country_list],
                value='Australia', id='attractions-dropdown', multi=False,
                style={'backgroundColor': '#deb522', 'color': 'black'}
            ),
            # 查詢按鈕
            html.Button(
                "查詢", id='attractions-submit', n_clicks=0, className="btn btn-primary",
                style={'backgroundColor': '#deb522','color': 'black','fontWeight': 'bold',
                       'marginTop': '10px','padding': '6px 16px','borderRadius': '6px','border': 'none','cursor': 'pointer'}
            ),
            # 顯示景點列表與地圖的區域 (包在dcc.loading裡面就會在載入時顯示載入動畫)
            dcc.Loading(
                id="attractions-loading", type="circle", color="#deb522", fullscreen=False,
                children=[html.Div(id='attractions-output-container', style={'overflow-x': 'auto','marginTop': '10px'}),
                          html.Div(id='attractions-map-container', style={'height': '600px','marginTop': '16px'})]
            )
        ])
    return html.Div("選擇的標籤頁不存在。", style={'color': 'white'})

####################################
#### Overview 頁面圖表 callbacks ####
####################################
# 長條圖（Bar Chart）
@app.callback(
    Output('tabs-content-1', 'children'),
    [Input('dropdown-bar-1', 'value'), Input('current-page', 'data')]
)
def update_bar_chart(dropdown_value, tab):
    # 只在 "overview" 分頁時才更新圖表，否則不動
    if tab != 'overview':
        return no_update
    
    # 載入旅遊資料集
    df = load_data('travel')
    
    # 若使用者沒有選擇任何國家（dropdown_value=None），就用預設值
    geo = dropdown_value or DEFAULTS["bar1_geo"]
    
    # 呼叫自訂函數生成 bar 圖
    fig1 = generate_bar(df, geo)
    return html.Div([dcc.Graph(id='graph1', figure=fig1)], style={'width': '90%','display': 'inline-block'})

# 圓餅圖（Pie Chart）
@app.callback(
    Output('tabs-content-2', 'children'),
    [Input('dropdown-pie-1', 'value'), Input('dropdown-pie-2', 'value'), Input('current-page', 'data')]
)
def update_pie_chart(dropdown_value_1, dropdown_value_2, tab):
    if tab != 'overview':
        return no_update
    df = load_data('travel')
    
    # 沒有選國家/欄位就用 DEFAULTS 的設定
    geo = dropdown_value_1 or DEFAULTS["pie1_geo"]
    field = dropdown_value_2 or DEFAULTS["pie2_field"]
    
    # 呼叫自訂函數生成圓餅圖
    fig2 = generate_pie(df, geo, field)
    return html.Div([dcc.Graph(id='graph2', figure=fig2)], style={'width': '90%','display': 'inline-block'})

# 地圖（Map Chart）
@app.callback(
    Output('tabs-content-3', 'children'),
    [Input('dropdown-map-1', 'value'), Input('dropdown-map-2', 'value'), Input('current-page', 'data')]
)
def update_map(dropdown_value_1, dropdown_value_2, tab):
    if tab != 'overview':
        return no_update
    df = load_data('travel')
    
    # 如果 dropdown_value_1 有值就用它；否則才用預設
    geo = dropdown_value_1 if dropdown_value_1 else DEFAULTS["map1_geo"]
    
    metric = dropdown_value_2 or DEFAULTS["map2_metric"]
    # 呼叫自訂函數生成地圖
    fig3 = generate_map(df, geo, metric)
    return html.Div([dcc.Graph(id='graph3', figure=fig3)], style={'width': '90%','display': 'inline-block'})

# 盒鬚圖（Box Chart）
@app.callback(
    Output('tabs-content-4', 'children'),
    [Input('dropdown-box-1', 'value'), Input('dropdown-box-2', 'value'), Input('current-page', 'data')]
)
def update_box_chart(dropdown_value_1, dropdown_value_2, tab):
    if tab != 'overview':
        return no_update
    df = load_data('travel')
    geo = dropdown_value_1 or DEFAULTS["box1_geo"]
    metric = dropdown_value_2 or DEFAULTS["box2_metric"]
    fig4 = generate_box(df, geo, metric)
    return html.Div([dcc.Graph(id='graph4', figure=fig4)], style={'width': '90%','display': 'inline-block'})

####################################
#### Trip Planner 頁面 callbacks ####
####################################
# 推薦國家表格
@app.callback(
    [Output('planner-table-container', 'children'),
     Output('planner-selected-countries', 'data')],
    [
        Input('planner-cost-min', 'value'),
        Input('planner-cost-max', 'value'),
        Input('planner-acc-types', 'value'),
        Input('planner-alert-max', 'value'),
        Input('planner-visa-only', 'value'),
        Input('w-safety', 'value'),
        Input('w-cost', 'value'),
        Input('current-page', 'data'),
    ]
)
def update_trip_planner_table(cost_min, cost_max, acc_types,
                              alert_max, visa_only,
                              w_safety, w_cost,
                              tab):
    if tab != 'planner':
        return no_update, no_update

    df_travel = travel_df.copy()

    # 1) 預處理與基本過濾
    cost_min, cost_max = sanitize_cost_bounds(cost_min, cost_max)
    df_travel = preprocess_travel_df(travel_df)
    df_travel = filter_by_cost_and_types(df_travel, cost_min, cost_max, acc_types)

    if df_travel.empty:
        return html.Div("沒有符合條件的國家。", style={'color': 'white'}), []

    # 從處理過後的 df_travel 取得國家列表
    matched_countries = sorted(df_travel['Destination'].dropna().unique().tolist())

    # 2) 取國家層資料並依 Alert / Visa 過濾
    df_country = pick_country_level(df_merged, matched_countries)
    df_country = filter_by_alert_and_visa(df_country, alert_max, visa_only)

    if df_country.empty:
        # ← 通常是被 Travel Alert 或 Visa 過濾到 0 筆
        return html.Div("沒有符合條件的國家（被 Travel Alert / Visa 過濾掉）。", style={'color': 'white'}), []

    # 聚合住宿成本到國家層級，並合併指標
    agg = df_travel.groupby('Destination', as_index=False).agg(
        trips=('Destination', 'count'),
        median_daily_acc_cost=('acc_daily_cost', 'median'),
        mean_daily_acc_cost=('acc_daily_cost', 'mean'),
        median_trip_acc_cost=('acc_trip_cost', 'median'),
        mean_trip_acc_cost=('acc_trip_cost', 'mean')
    )
    out = df_country.merge(agg, on='Destination', how='inner').rename(columns={'Destination': 'Country'})

    # 4) 計算分數（安全 + 成本）
    out = compute_scores(out, w_safety, w_cost)

    # 5) 排序、選前 5 名作為 compare_countries
    out = out.sort_values(by=['Score', 'Safety Index', 'adj_daily_acc_cost'],
                          ascending=[False, False, True])  # ← 高分、越安全越前面；成本越低越前面
    compare_countries = out['Country'].head(5).tolist()

    # 6) 輸出表格元件
    table_component = build_table_component(out)
    
    return table_component, compare_countries

# 產生雷達 / 長條 / 折線圖（前五名 + 全指標）
@app.callback(
    [Output('planner-compare-radar', 'children'),
     Output('planner-compare-bar', 'children'),
     Output('planner-compare-line', 'children')],
    [Input('planner-selected-countries', 'data'),
     Input('current-page', 'data')]
)
def update_trip_planner_comparison(countries, tab):
    if tab != 'planner':
        return no_update, no_update, no_update

    if not countries:
        msg = html.Div('請先透過上方條件找到至少一個國家。', style={'color': 'white'})
        return msg, msg, msg
    metrics = ALL_COMPARE_METRICS  # 預設比較所有指標
    df_result, limited_countries = prepare_country_compare_data(countries, metrics, df_merged)
    if df_result.empty or not limited_countries:
        msg = html.Div('所選國家沒有足夠的比較數據。', style={'color': 'white'})
        return msg, msg, msg

    radar_fig = build_compare_figure(df_result, 'radar', 'Trip Planner 雷達圖')
    bar_fig = build_compare_figure(df_result, 'bar', 'Trip Planner 長條圖')
    line_fig = build_compare_figure(df_result, 'line', 'Trip Planner 折線圖')

    return html.Div([dcc.Graph(figure=radar_fig)]), \
           html.Div([dcc.Graph(figure=bar_fig)]), \
           html.Div([dcc.Graph(figure=line_fig)])

###############################
#### Attractions callback ####
###############################
# 使用 geopy 套件將景點名稱轉換為經緯度，並在地圖上標示
@app.callback(
    [Output('attractions-output-container', 'children'),
     Output('attractions-map-container', 'children')],
    [Input('attractions-submit', 'n_clicks'), Input('current-page', 'data')],
    [State('attractions-dropdown', 'value')],
    prevent_initial_call=True
)
def update_attractions_output(n_clicks, tab, chosen_country):
    if tab != 'attractions':
        raise PreventUpdate
    if n_clicks == 0 or not chosen_country:
        return (html.Div("請選擇一個國家並按下查詢。", style={'color': 'white'}), no_update)

    # 根據使用者選的國家，過濾出該國家的景點資料
    chosen_df = attractions_df[attractions_df['country'] == chosen_country].copy()

    # 建立表格元件，顯示該國家的所有景點資訊
    table = dash_table.DataTable(
        data=chosen_df.to_dict('records'), page_size=10,
        style_data={'backgroundColor': '#deb522', 'color': 'black'},
        style_header={'backgroundColor': 'black', 'color': '#deb522', 'fontWeight': 'bold'}
    )

    # 建立地理編碼器：用來把地名轉成經緯度
    geolocator = Nominatim(user_agent="my_dash_app")
    # RateLimiter：避免短時間太多請求被伺服器擋掉（每次至少間隔 1 秒）
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    points = [] # ← 用來存放每個景點的名稱與座標
    
    # 對每一筆景點資料進行地理編碼
    for _, r in chosen_df.iterrows():
        name = str(r['attraction'])
        try:
            location = geocode(name) # ← 嘗試查詢景點的經緯度
            if location:
                # 若成功取得經緯度，就存進 points 清單中
                points.append({'name': name, 'lat': location.latitude, 'lng': location.longitude})
        except Exception:
            # 若查詢失敗（例如找不到該景點），就跳過該筆資料
            continue

    if not points:
        return table, html.Div("選定國家目前沒有可用座標的景點。", style={'color': 'white'})

    # 建立地圖底圖圖層（使用 OpenStreetMap）
    tile_layer = dl.TileLayer(
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    )
    
    # 為每個景點建立一個 Marker（地圖上的小釘子），滑鼠移過去會顯示名稱
    markers = [dl.Marker(position=[p['lat'], p['lng']], children=dl.Tooltip(p['name'])) for p in points]

    # 取出所有經緯度
    lats = [p['lat'] for p in points]; lngs = [p['lng'] for p in points]
    # 計算地圖顯示的範圍（最南西角 ~ 最北東角）
    south, west = min(lats), min(lngs); north, east = max(lats), max(lngs)
    bounds = [[south, west], [north, east]]

    if len(points) == 1:
        # 若只有一個點 → 直接置中顯示
        center = [points[0]['lat'], points[0]['lng']]
        the_map = dl.Map(id=f"map-{hash(str(bounds))}",
                         children=[tile_layer, dl.LayerGroup(markers)],
                         center=center, zoom=10, style={'width': '100%','height': '600px'})
    else:
        # 多個點 → 根據 bounds 自動調整視野
        the_map = dl.Map(id=f"map-{hash(str(bounds))}",
                         children=[tile_layer, dl.LayerGroup(markers)],
                         bounds=bounds, style={'width': '100%','height': '600px'})
    return table, the_map

####################################
#### 熱門餐廳卡片 callback ####
####################################
@app.callback(
    Output('popular-restaurants-container', 'children'),
    [Input('current-page', 'data')]
)
def update_popular_restaurants(current_page):
    """動態生成熱門餐廳卡片"""
    # 隨機選擇5個4-5星餐廳
    selected_restaurants = get_random_top_restaurants(5)

    # 建立餐廳卡片列表
    cards = []
    for _, restaurant in selected_restaurants.iterrows():
        card = dbc.Card([
            dbc.CardBody([
                html.H4(restaurant['Name'], style={
                    'color': '#deb522',
                    'fontWeight': 'bold',
                    'marginBottom': '10px'
                }),
                html.P(restaurant['JapaneseName'], style={
                    'color': '#999',
                    'fontSize': '14px',
                    'marginBottom': '15px'
                }),
                html.Div([
                    html.I(className='fas fa-map-marker-alt', style={'color': '#deb522', 'marginRight': '8px'}),
                    html.Span(f"車站: {restaurant['Station']}", style={'color': 'white'})
                ], style={'marginBottom': '8px'}),
                html.Div([
                    html.I(className='fas fa-utensils', style={'color': '#deb522', 'marginRight': '8px'}),
                    html.Span(f"{restaurant['FirstCategory']} / {restaurant['SecondCategory']}", style={'color': 'white'})
                ], style={'marginBottom': '8px'}),
                html.Div([
                    html.I(className='fas fa-star', style={'color': '#deb522', 'marginRight': '8px'}),
                    html.Span(f"評分: {restaurant['TotalRating']:.2f}", style={'color': 'white', 'fontWeight': 'bold'})
                ], style={'marginBottom': '0px'}),
            ])
        ], style={
            'backgroundColor': '#2a2a2a',
            'border': '2px solid #deb522',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(222, 181, 34, 0.2)',
            'transition': 'transform 0.2s',
            'height': '100%'
        })
        cards.append(dbc.Col(card, width=12, md=6, lg=2, style={'marginBottom': '15px'}))

    return dbc.Row(cards, justify='center', style={'margin': '0 auto', 'maxWidth': '1400px'})

if __name__ == '__main__':
    app.run(debug=False)
