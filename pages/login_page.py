from dash import html, dcc
import dash_bootstrap_components as dbc

def create_login_layout():
    
    return html.Div([
        # 背景裝飾元素
        html.Div(style={
            'position': 'fixed',
            'top': '-50%',
            'left': '-50%',
            'width': '200%',
            'height': '200%',
            'background': 'radial-gradient(circle at 20% 50%, rgba(222, 181, 34, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(222, 181, 34, 0.08) 0%, transparent 50%)',
            'zIndex': '0',
            'pointerEvents': 'none'
        }),

        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        # Logo 和標題區域
                        html.Div([
                            html.Div([
                                html.Img(
                                    src='/assets/logo.png',
                                    style={
                                        'height': '100px',
                                        'marginBottom': '25px',
                                        'filter': 'drop-shadow(0 4px 8px rgba(222, 181, 34, 0.4))',
                                        'animation': 'fadeInDown 0.8s ease-out'
                                    }
                                ),
                            ], style={'textAlign': 'center'}),

                            html.H1(
                                '柔成員的旅遊平台',
                                style={
                                    'textAlign': 'center',
                                    'background': 'linear-gradient(135deg, #deb522 0%, #f5d876 100%)',
                                    'WebkitBackgroundClip': 'text',
                                    'WebkitTextFillColor': 'transparent',
                                    'backgroundClip': 'text',
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
                                    'color': '#999',
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
                                        'color': '#deb522',
                                        'marginBottom': '20px'
                                    }),
                                    html.H3('歡迎回來', style={
                                        'color': '#fff',
                                        'fontWeight': '600',
                                        'marginBottom': '10px'
                                    }),
                                    html.P('請登入您的帳戶', style={
                                        'color': '#888',
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
                                            'color': '#deb522',
                                            'fontSize': '1.1rem'
                                        }),
                                        dbc.Input(
                                            id='login-username',
                                            type='text',
                                            placeholder='使用者名稱',
                                            style={
                                                'backgroundColor': 'rgba(255, 255, 255, 0.05)',
                                                'color': 'white',
                                                'border': '2px solid rgba(222, 181, 34, 0.3)',
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
                                            'color': '#deb522',
                                            'fontSize': '1.1rem'
                                        }),
                                        dbc.Input(
                                            id='login-password',
                                            type='password',
                                            placeholder='密碼',
                                            style={
                                                'backgroundColor': 'rgba(255, 255, 255, 0.05)',
                                                'color': 'white',
                                                'border': '2px solid rgba(222, 181, 34, 0.3)',
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
                                        'color': '#aaa',
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
                                        'background': 'linear-gradient(135deg, #deb522 0%, #f5d876 100%)',
                                        'border': 'none',
                                        'fontWeight': '700',
                                        'fontSize': '1.1rem',
                                        'padding': '15px',
                                        'borderRadius': '12px',
                                        'marginBottom': '25px',
                                        'boxShadow': '0 4px 15px rgba(222, 181, 34, 0.4)',
                                        'transition': 'all 0.3s ease',
                                        'cursor': 'pointer',
                                        'color': '#000'
                                    }
                                ),

                                # 分隔線
                                html.Div([
                                    html.Div(style={
                                        'flex': '1',
                                        'height': '1px',
                                        'background': 'rgba(255, 255, 255, 0.1)'
                                    }),
                                    html.Span('或', style={
                                        'color': '#666',
                                        'padding': '0 15px',
                                        'fontSize': '0.85rem'
                                    }),
                                    html.Div(style={
                                        'flex': '1',
                                        'height': '1px',
                                        'background': 'rgba(255, 255, 255, 0.1)'
                                    }),
                                ], style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'marginBottom': '25px'
                                }),

                                # 註冊連結
                                html.Div([
                                    html.Span('還沒有帳號？', style={'color': '#888', 'marginRight': '8px'}),
                                    html.A([
                                        '立即註冊',
                                        html.I(className='fas fa-arrow-right', style={'marginLeft': '8px', 'fontSize': '0.85rem'})
                                    ], href='#', id='register-link', style={
                                        'color': '#deb522',
                                        'textDecoration': 'none',
                                        'fontWeight': '600',
                                        'transition': 'all 0.3s ease'
                                    })
                                ], style={'textAlign': 'center'}),
                            ], style={'padding': '45px 40px'})
                        ], style={
                            'backgroundColor': 'rgba(26, 26, 26, 0.95)',
                            'border': '1px solid rgba(222, 181, 34, 0.2)',
                            'borderRadius': '24px',
                            'backdropFilter': 'blur(10px)',
                            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(222, 181, 34, 0.1)',
                            'animation': 'slideUp 0.8s ease-out',
                            'marginBottom': '30px'
                        }),

                        # 測試帳號提示
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-info-circle', style={
                                    'color': '#deb522',
                                    'marginRight': '10px',
                                    'fontSize': '1.1rem'
                                }),
                                html.Strong('測試帳號', style={'color': '#deb522'})
                            ], style={
                                'textAlign': 'center',
                                'marginBottom': '12px',
                                'fontSize': '1rem'
                            }),
                            html.Div([
                                html.Div([
                                    html.I(className='fas fa-user-shield', style={'marginRight': '8px', 'color': '#deb522'}),
                                    html.Span('admin', style={'fontWeight': '600', 'color': '#fff'}),
                                    html.Span(' / ', style={'color': '#555', 'margin': '0 5px'}),
                                    html.Span('admin123', style={'color': '#aaa'})
                                ], style={'marginBottom': '8px'}),
                                html.Div([
                                    html.I(className='fas fa-user', style={'marginRight': '8px', 'color': '#deb522'}),
                                    html.Span('demo', style={'fontWeight': '600', 'color': '#fff'}),
                                    html.Span(' / ', style={'color': '#555', 'margin': '0 5px'}),
                                    html.Span('demo123', style={'color': '#aaa'})
                                ])
                            ], style={'fontSize': '0.9rem', 'textAlign': 'center'})
                        ], style={
                            'backgroundColor': 'rgba(222, 181, 34, 0.05)',
                            'border': '1px solid rgba(222, 181, 34, 0.2)',
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
            'background': 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%)',
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
        # 背景裝飾元素
        html.Div(style={
            'position': 'fixed',
            'top': '-50%',
            'left': '-50%',
            'width': '200%',
            'height': '200%',
            'background': 'radial-gradient(circle at 20% 50%, rgba(222, 181, 34, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(222, 181, 34, 0.08) 0%, transparent 50%)',
            'zIndex': '0',
            'pointerEvents': 'none'
        }),

        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        # Logo 和標題區域
                        html.Div([
                            html.Div([
                                html.Img(
                                    src='/assets/logo.png',
                                    style={
                                        'height': '90px',
                                        'marginBottom': '25px',
                                        'filter': 'drop-shadow(0 4px 8px rgba(222, 181, 34, 0.4))',
                                        'animation': 'fadeInDown 0.8s ease-out'
                                    }
                                ),
                            ], style={'textAlign': 'center'}),

                            html.H1(
                                '建立新帳號',
                                style={
                                    'textAlign': 'center',
                                    'background': 'linear-gradient(135deg, #deb522 0%, #f5d876 100%)',
                                    'WebkitBackgroundClip': 'text',
                                    'WebkitTextFillColor': 'transparent',
                                    'backgroundClip': 'text',
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
                                    'color': '#999',
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
                                        'color': '#deb522',
                                        'marginBottom': '15px'
                                    }),
                                    html.P('填寫資訊完成註冊', style={
                                        'color': '#888',
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
                                            'color': '#deb522',
                                            'fontSize': '1rem'
                                        }),
                                        dbc.Input(
                                            id='register-username',
                                            type='text',
                                            placeholder='使用者名稱',
                                            style={
                                                'backgroundColor': 'rgba(255, 255, 255, 0.05)',
                                                'color': 'white',
                                                'border': '2px solid rgba(222, 181, 34, 0.3)',
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
                                            'color': '#deb522',
                                            'fontSize': '1rem'
                                        }),
                                        dbc.Input(
                                            id='register-email',
                                            type='email',
                                            placeholder='電子郵件（選填）',
                                            style={
                                                'backgroundColor': 'rgba(255, 255, 255, 0.05)',
                                                'color': 'white',
                                                'border': '2px solid rgba(222, 181, 34, 0.3)',
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
                                            'color': '#deb522',
                                            'fontSize': '1rem'
                                        }),
                                        dbc.Input(
                                            id='register-password',
                                            type='password',
                                            placeholder='密碼（至少 6 位）',
                                            style={
                                                'backgroundColor': 'rgba(255, 255, 255, 0.05)',
                                                'color': 'white',
                                                'border': '2px solid rgba(222, 181, 34, 0.3)',
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
                                            'color': '#deb522',
                                            'fontSize': '1rem'
                                        }),
                                        dbc.Input(
                                            id='register-password-confirm',
                                            type='password',
                                            placeholder='確認密碼',
                                            style={
                                                'backgroundColor': 'rgba(255, 255, 255, 0.05)',
                                                'color': 'white',
                                                'border': '2px solid rgba(222, 181, 34, 0.3)',
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
                                        'background': 'linear-gradient(135deg, #deb522 0%, #f5d876 100%)',
                                        'border': 'none',
                                        'fontWeight': '700',
                                        'fontSize': '1.05rem',
                                        'padding': '14px',
                                        'borderRadius': '12px',
                                        'marginBottom': '25px',
                                        'boxShadow': '0 4px 15px rgba(222, 181, 34, 0.4)',
                                        'transition': 'all 0.3s ease',
                                        'cursor': 'pointer',
                                        'color': '#000'
                                    }
                                ),

                                # 分隔線
                                html.Div([
                                    html.Div(style={
                                        'flex': '1',
                                        'height': '1px',
                                        'background': 'rgba(255, 255, 255, 0.1)'
                                    }),
                                    html.Span('或', style={
                                        'color': '#666',
                                        'padding': '0 15px',
                                        'fontSize': '0.85rem'
                                    }),
                                    html.Div(style={
                                        'flex': '1',
                                        'height': '1px',
                                        'background': 'rgba(255, 255, 255, 0.1)'
                                    }),
                                ], style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'marginBottom': '25px'
                                }),

                                # 返回登入連結
                                html.Div([
                                    html.Span('已有帳號？', style={'color': '#888', 'marginRight': '8px'}),
                                    html.A([
                                        '返回登入',
                                        html.I(className='fas fa-arrow-left', style={'marginLeft': '8px', 'fontSize': '0.85rem'})
                                    ], href='#', id='back-to-login-link', style={
                                        'color': '#deb522',
                                        'textDecoration': 'none',
                                        'fontWeight': '600',
                                        'transition': 'all 0.3s ease'
                                    })
                                ], style={'textAlign': 'center'}),
                            ], style={'padding': '40px 35px'})
                        ], style={
                            'backgroundColor': 'rgba(26, 26, 26, 0.95)',
                            'border': '1px solid rgba(222, 181, 34, 0.2)',
                            'borderRadius': '24px',
                            'backdropFilter': 'blur(10px)',
                            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(222, 181, 34, 0.1)',
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
            'background': 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%)',
            'minHeight': '100vh',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'padding': '20px',
            'position': 'relative',
            'overflow': 'hidden'
        })
    ], style={'position': 'relative'})
