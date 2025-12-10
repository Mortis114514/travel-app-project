from dash import html, dcc
import dash_bootstrap_components as dbc

def create_login_layout():

    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        # 標題區域
                        html.Div([
                            html.H1(
                                '旅遊平台',
                                style={
                                    'textAlign': 'center',
                                    'color': '#003580',
                                    'marginBottom': '10px',
                                    'fontWeight': '800',
                                    'fontSize': '2.2rem',
                                    'letterSpacing': '1px',
                                    'animation': 'fadeIn 1s ease-out'
                                }
                            ),
                            html.P(
                                'Roger Travel Platform',
                                style={
                                    'textAlign': 'center',
                                    'color': '#4A5568',
                                    'marginBottom': '50px',
                                    'fontSize': '0.95rem',
                                    'letterSpacing': '2px',
                                    'textTransform': 'uppercase',
                                    'animation': 'fadeIn 1.2s ease-out'
                                }
                            ),
                        ]),

                        # 登入表單卡片
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className='fas fa-user-circle', style={
                                        'fontSize': '3rem',
                                        'color': '#003580',
                                        'marginBottom': '20px'
                                    }),
                                    html.H3('歡迎回來', style={
                                        'color': '#1A1A1A',
                                        'fontWeight': '600',
                                        'marginBottom': '10px'
                                    }),
                                    html.P('請登入您的帳戶', style={
                                        'color': '#4A5568',
                                        'fontSize': '0.9rem',
                                        'marginBottom': '35px'
                                    })
                                ], style={'textAlign': 'center'}),

                                # 錯誤訊息顯示區
                                html.Div(id='login-error-message', style={'marginBottom': '20px'}),

                                # 使用者名稱
                                html.Div([
                                    html.Div([
                                        html.I(className='fas fa-user', style={
                                            'position': 'absolute',
                                            'left': '15px',
                                            'top': '50%',
                                            'transform': 'translateY(-50%)',
                                            'color': '#003580',
                                            'fontSize': '1.1rem'
                                        }),
                                        dbc.Input(
                                            id='login-username',
                                            type='text',
                                            placeholder='使用者名稱',
                                            style={
                                                'backgroundColor': '#FFFFFF',
                                                'color': '#1A1A1A',
                                                'border': '2px solid #E8ECEF',
                                                'borderRadius': '12px',
                                                'padding': '15px 15px 15px 45px',
                                                'fontSize': '1rem',
                                                'transition': 'all 0.3s ease'
                                            }
                                        ),
                                    ], style={'position': 'relative', 'marginBottom': '20px'})
                                ]),

                                # 密碼
                                html.Div([
                                    html.Div([
                                        html.I(className='fas fa-lock', style={
                                            'position': 'absolute',
                                            'left': '15px',
                                            'top': '50%',
                                            'transform': 'translateY(-50%)',
                                            'color': '#003580',
                                            'fontSize': '1.1rem'
                                        }),
                                        dbc.Input(
                                            id='login-password',
                                            type='password',
                                            placeholder='密碼',
                                            style={
                                                'backgroundColor': '#FFFFFF',
                                                'color': '#1A1A1A',
                                                'border': '2px solid #E8ECEF',
                                                'borderRadius': '12px',
                                                'padding': '15px 15px 15px 45px',
                                                'fontSize': '1rem',
                                                'transition': 'all 0.3s ease'
                                            }
                                        ),
                                    ], style={'position': 'relative', 'marginBottom': '25px'})
                                ]),

                                # 記住我選項
                                html.Div([
                                    dbc.Checkbox(
                                        id='login-remember',
                                        label='',
                                        value=False,
                                        style={'display': 'inline-block', 'marginRight': '8px'}
                                    ),
                                    html.Label('記住我 30 天', style={
                                        'color': '#4A5568',
                                        'fontSize': '0.9rem',
                                        'cursor': 'pointer'
                                    })
                                ], style={'marginBottom': '30px'}),

                                # 登入按鈕
                                dbc.Button(
                                    [
                                        html.I(className='fas fa-sign-in-alt', style={'marginRight': '10px'}),
                                        '登入'
                                    ],
                                    id='login-button',
                                    className='w-100',
                                    style={
                                        'background': 'linear-gradient(135deg, #003580 0%, #0051A8 100%)',
                                        'border': 'none',
                                        'fontWeight': '700',
                                        'fontSize': '1.1rem',
                                        'padding': '15px',
                                        'borderRadius': '50px',
                                        'marginBottom': '25px',
                                        'boxShadow': '0 4px 12px rgba(0, 53, 128, 0.3)',
                                        'transition': 'all 0.3s ease',
                                        'cursor': 'pointer',
                                        'color': '#FFFFFF'
                                    }
                                ),

                                # 分隔線
                                html.Div([
                                    html.Div(style={
                                        'flex': '1',
                                        'height': '1px',
                                        'background': '#E8ECEF'
                                    }),
                                    html.Span('或', style={
                                        'color': '#4A5568',
                                        'padding': '0 15px',
                                        'fontSize': '0.85rem'
                                    }),
                                    html.Div(style={
                                        'flex': '1',
                                        'height': '1px',
                                        'background': '#E8ECEF'
                                    }),
                                ], style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'marginBottom': '25px'
                                }),

                                # 註冊連結
                                html.Div([
                                    html.Span('還沒有帳號？', style={'color': '#4A5568', 'marginRight': '8px'}),
                                    html.A([
                                        '立即註冊',
                                        html.I(className='fas fa-arrow-right', style={'marginLeft': '8px', 'fontSize': '0.85rem'})
                                    ], href='#', id='register-link', style={
                                        'color': '#003580',
                                        'textDecoration': 'none',
                                        'fontWeight': '600',
                                        'transition': 'all 0.3s ease'
                                    })
                                ], style={'textAlign': 'center'}),
                            ], style={'padding': '45px 40px'})
                        ], style={
                            'backgroundColor': '#FFFFFF',
                            'border': '1px solid #E8ECEF',
                            'borderRadius': '24px',
                            'backdropFilter': 'blur(10px)',
                            'boxShadow': '0 8px 32px rgba(0, 53, 128, 0.1), 0 2px 8px rgba(0, 53, 128, 0.06)',
                            'animation': 'slideUp 0.8s ease-out',
                            'marginBottom': '30px'
                        }),

                        # 測試帳號提示
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-info-circle', style={
                                    'color': '#003580',
                                    'marginRight': '10px',
                                    'fontSize': '1.1rem'
                                }),
                                html.Strong('測試帳號', style={'color': '#003580'})
                            ], style={
                                'textAlign': 'center',
                                'marginBottom': '12px',
                                'fontSize': '1rem'
                            }),
                            html.Div([
                                html.Div([
                                    html.I(className='fas fa-user-shield', style={'marginRight': '8px', 'color': '#003580'}),
                                    html.Span('admin', style={'fontWeight': '600', 'color': '#1A1A1A'}),
                                    html.Span(' / ', style={'color': '#4A5568', 'margin': '0 5px'}),
                                    html.Span('admin123', style={'color': '#4A5568'})
                                ], style={'marginBottom': '8px'}),
                                html.Div([
                                    html.I(className='fas fa-user', style={'marginRight': '8px', 'color': '#003580'}),
                                    html.Span('demo', style={'fontWeight': '600', 'color': '#1A1A1A'}),
                                    html.Span(' / ', style={'color': '#4A5568', 'margin': '0 5px'}),
                                    html.Span('demo123', style={'color': '#4A5568'})
                                ])
                            ], style={'fontSize': '0.9rem', 'textAlign': 'center'})
                        ], style={
                            'backgroundColor': 'rgba(0, 53, 128, 0.05)',
                            'border': '1px solid rgba(0, 53, 128, 0.15)',
                            'borderRadius': '16px',
                            'padding': '20px',
                            'animation': 'fadeIn 1.5s ease-out'
                        }),

                    ], style={
                        'maxWidth': '480px',
                        'margin': '0 auto',
                        'padding': '40px 20px',
                        'position': 'relative',
                        'zIndex': '1'
                    })
                ], width=12)
            ], justify="center")
        ], style={
            'background': '#F2F6FA',
            'minHeight': '100vh',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'padding': '20px',
            'position': 'relative',
            'overflow': 'hidden'
        })
    ], style={'position': 'relative'})

def create_register_layout():
    """建立註冊頁面布局 - 專業設計版"""
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        # 標題區域
                        html.Div([
                            html.H1(
                                '建立新帳號',
                                style={
                                    'textAlign': 'center',
                                    'color': '#003580',
                                    'marginBottom': '10px',
                                    'fontWeight': '800',
                                    'fontSize': '2rem',
                                    'animation': 'fadeIn 1s ease-out'
                                }
                            ),
                            html.P(
                                '開始您的數據分析之旅',
                                style={
                                    'textAlign': 'center',
                                    'color': '#4A5568',
                                    'marginBottom': '40px',
                                    'fontSize': '0.95rem',
                                    'animation': 'fadeIn 1.2s ease-out'
                                }
                            ),
                        ]),

                        # 註冊表單卡片
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className='fas fa-user-plus', style={
                                        'fontSize': '2.5rem',
                                        'color': '#003580',
                                        'marginBottom': '15px'
                                    }),
                                    html.P('填寫資訊完成註冊', style={
                                        'color': '#4A5568',
                                        'fontSize': '0.9rem',
                                        'marginBottom': '30px'
                                    })
                                ], style={'textAlign': 'center'}),

                                # 錯誤/成功訊息顯示區
                                html.Div(id='register-message', style={'marginBottom': '20px'}),

                                # 使用者名稱
                                html.Div([
                                    html.Div([
                                        html.I(className='fas fa-user', style={
                                            'position': 'absolute',
                                            'left': '15px',
                                            'top': '50%',
                                            'transform': 'translateY(-50%)',
                                            'color': '#003580',
                                            'fontSize': '1rem'
                                        }),
                                        dbc.Input(
                                            id='register-username',
                                            type='text',
                                            placeholder='使用者名稱',
                                            style={
                                                'backgroundColor': '#FFFFFF',
                                                'color': '#1A1A1A',
                                                'border': '2px solid #E8ECEF',
                                                'borderRadius': '12px',
                                                'padding': '14px 15px 14px 45px',
                                                'fontSize': '0.95rem',
                                                'transition': 'all 0.3s ease'
                                            }
                                        ),
                                    ], style={'position': 'relative', 'marginBottom': '18px'})
                                ]),

                                # Email
                                html.Div([
                                    html.Div([
                                        html.I(className='fas fa-envelope', style={
                                            'position': 'absolute',
                                            'left': '15px',
                                            'top': '50%',
                                            'transform': 'translateY(-50%)',
                                            'color': '#003580',
                                            'fontSize': '1rem'
                                        }),
                                        dbc.Input(
                                            id='register-email',
                                            type='email',
                                            placeholder='電子郵件（選填）',
                                            style={
                                                'backgroundColor': '#FFFFFF',
                                                'color': '#1A1A1A',
                                                'border': '2px solid #E8ECEF',
                                                'borderRadius': '12px',
                                                'padding': '14px 15px 14px 45px',
                                                'fontSize': '0.95rem',
                                                'transition': 'all 0.3s ease'
                                            }
                                        ),
                                    ], style={'position': 'relative', 'marginBottom': '18px'})
                                ]),

                                # 密碼
                                html.Div([
                                    html.Div([
                                        html.I(className='fas fa-lock', style={
                                            'position': 'absolute',
                                            'left': '15px',
                                            'top': '50%',
                                            'transform': 'translateY(-50%)',
                                            'color': '#003580',
                                            'fontSize': '1rem'
                                        }),
                                        dbc.Input(
                                            id='register-password',
                                            type='password',
                                            placeholder='密碼（至少 6 位）',
                                            style={
                                                'backgroundColor': '#FFFFFF',
                                                'color': '#1A1A1A',
                                                'border': '2px solid #E8ECEF',
                                                'borderRadius': '12px',
                                                'padding': '14px 15px 14px 45px',
                                                'fontSize': '0.95rem',
                                                'transition': 'all 0.3s ease'
                                            }
                                        ),
                                    ], style={'position': 'relative', 'marginBottom': '18px'})
                                ]),

                                # 確認密碼
                                html.Div([
                                    html.Div([
                                        html.I(className='fas fa-lock-open', style={
                                            'position': 'absolute',
                                            'left': '15px',
                                            'top': '50%',
                                            'transform': 'translateY(-50%)',
                                            'color': '#003580',
                                            'fontSize': '1rem'
                                        }),
                                        dbc.Input(
                                            id='register-password-confirm',
                                            type='password',
                                            placeholder='確認密碼',
                                            style={
                                                'backgroundColor': '#FFFFFF',
                                                'color': '#1A1A1A',
                                                'border': '2px solid #E8ECEF',
                                                'borderRadius': '12px',
                                                'padding': '14px 15px 14px 45px',
                                                'fontSize': '0.95rem',
                                                'transition': 'all 0.3s ease'
                                            }
                                        ),
                                    ], style={'position': 'relative', 'marginBottom': '30px'})
                                ]),

                                # 註冊按鈕
                                dbc.Button(
                                    [
                                        html.I(className='fas fa-user-plus', style={'marginRight': '10px'}),
                                        '立即註冊'
                                    ],
                                    id='register-button',
                                    className='w-100',
                                    style={
                                        'background': 'linear-gradient(135deg, #003580 0%, #0051A8 100%)',
                                        'border': 'none',
                                        'fontWeight': '700',
                                        'fontSize': '1.05rem',
                                        'padding': '14px',
                                        'borderRadius': '50px',
                                        'marginBottom': '25px',
                                        'boxShadow': '0 4px 12px rgba(0, 53, 128, 0.3)',
                                        'transition': 'all 0.3s ease',
                                        'cursor': 'pointer',
                                        'color': '#FFFFFF'
                                    }
                                ),

                                # 分隔線
                                html.Div([
                                    html.Div(style={
                                        'flex': '1',
                                        'height': '1px',
                                        'background': '#E8ECEF'
                                    }),
                                    html.Span('或', style={
                                        'color': '#4A5568',
                                        'padding': '0 15px',
                                        'fontSize': '0.85rem'
                                    }),
                                    html.Div(style={
                                        'flex': '1',
                                        'height': '1px',
                                        'background': '#E8ECEF'
                                    }),
                                ], style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'marginBottom': '25px'
                                }),

                                # 返回登入連結
                                html.Div([
                                    html.Span('已有帳號？', style={'color': '#4A5568', 'marginRight': '8px'}),
                                    html.A([
                                        '返回登入',
                                        html.I(className='fas fa-arrow-left', style={'marginLeft': '8px', 'fontSize': '0.85rem'})
                                    ], href='#', id='back-to-login-link', style={
                                        'color': '#003580',
                                        'textDecoration': 'none',
                                        'fontWeight': '600',
                                        'transition': 'all 0.3s ease'
                                    })
                                ], style={'textAlign': 'center'}),
                            ], style={'padding': '40px 35px'})
                        ], style={
                            'backgroundColor': '#FFFFFF',
                            'border': '1px solid #E8ECEF',
                            'borderRadius': '24px',
                            'backdropFilter': 'blur(10px)',
                            'boxShadow': '0 8px 32px rgba(0, 53, 128, 0.1), 0 2px 8px rgba(0, 53, 128, 0.06)',
                            'animation': 'slideUp 0.8s ease-out'
                        }),

                    ], style={
                        'maxWidth': '500px',
                        'margin': '0 auto',
                        'padding': '40px 20px',
                        'position': 'relative',
                        'zIndex': '1'
                    })
                ], width=12)
            ], justify="center")
        ], style={
            'background': '#F2F6FA',
            'minHeight': '100vh',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'padding': '20px',
            'position': 'relative',
            'overflow': 'hidden'
        })
    ], style={'position': 'relative'})
