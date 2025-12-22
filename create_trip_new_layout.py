# New drag-and-drop Create Trip layout
# This file contains the new layout code to replace create_trip_layout()

def create_draggable_favorite_item(fav):
    """Create a draggable favorite item"""
    icon_map = {
        'restaurant': 'fas fa-utensils',
        'hotel': 'fas fa-hotel',
        'attraction': 'fas fa-map-marker-alt'
    }

    return html.Div([
        html.I(className=icon_map.get(fav['item_type'], 'fas fa-map-pin'),
               style={'marginRight': '0.75rem', 'color': '#deb522', 'fontSize': '1.1rem'}),
        html.Div([
            html.Div(fav['item_name'], style={'fontWeight': '500', 'color': '#003580'}),
            html.Div(fav['item_type'].capitalize(), style={'fontSize': '0.85rem', 'color': '#888'})
        ], style={'flex': '1'}),
        html.I(className='fas fa-grip-vertical', style={'color': '#ccc', 'cursor': 'grab'})
    ],
    id={'type': 'draggable-fav', 'item-type': fav['item_type'], 'item-id': fav['item_id']},
    draggable='true',
    **{
        'data-item-type': fav['item_type'],
        'data-item-id': str(fav['item_id']),
        'data-item-name': fav['item_name']
    },
    style={
        'display': 'flex',
        'alignItems': 'center',
        'padding': '1rem',
        'marginBottom': '0.5rem',
        'backgroundColor': '#F8F9FA',
        'border': '1px solid #E8ECEF',
        'borderRadius': '8px',
        'cursor': 'grab',
        'transition': 'all 0.2s'
    },
    className='draggable-item')


def create_trip_layout_v2(session_data=None):
    """Create Trip page layout with drag-and-drop interface"""
    from utils.favorites import get_user_favorites
    from utils.auth import get_session

    # Get user's favorites
    favorites_by_type = {'restaurant': [], 'hotel': [], 'attraction': []}
    user_id = None

    if session_data and 'session_id' in session_data:
        user_id = get_session(session_data['session_id'])
        if user_id:
            favorites = get_user_favorites(user_id)
            if favorites:
                # Organize by type
                for fav in favorites:
                    fav_type = fav['item_type']
                    if fav_type in favorites_by_type:
                        favorites_by_type[fav_type].append(fav)

    return html.Div([
        # Header (unchanged)
        html.Div([
            html.Div([
                html.Div([
                    html.Button([
                        html.I(className='fas fa-arrow-left'),
                        html.Span('Back', style={'marginLeft': '8px'})
                    ], id={'type': 'back-btn', 'index': 'create-trip'}, className='btn-back'),
                    html.H1('Create Your Trip', style={
                        'color': '#003580',
                        'marginLeft': '2rem',
                        'fontSize': '2rem',
                        'fontWeight': 'bold'
                    })
                ], style={'display': 'flex', 'alignItems': 'center'}),
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

        # Main content
        html.Div([
            html.Div([
                # Top Section: Trip Info Form
                html.Div([
                    html.H2('Trip Information', style={
                        'color': '#003580',
                        'fontSize': '1.5rem',
                        'fontWeight': '600',
                        'marginBottom': '1.5rem'
                    }),

                    # Trip Name
                    html.Div([
                        html.Label('Trip Name *'),
                        dcc.Input(
                            id='trip-name-input',
                            type='text',
                            placeholder='e.g., Kyoto Summer Adventure 2024',
                            style={'width': '100%', 'padding': '0.75rem', 'borderRadius': '8px', 'border': '1px solid #ddd'}
                        )
                    ], style={'marginBottom': '1rem'}),

                    # Dates
                    html.Div([
                        html.Div([
                            html.Label('Start Date *'),
                            dcc.DatePickerSingle(id='trip-start-date', placeholder='Select start date', display_format='YYYY-MM-DD')
                        ], style={'flex': '1', 'marginRight': '1rem'}),
                        html.Div([
                            html.Label('End Date *'),
                            dcc.DatePickerSingle(id='trip-end-date', placeholder='Select end date', display_format='YYYY-MM-DD')
                        ], style={'flex': '1'})
                    ], style={'display': 'flex', 'marginBottom': '1rem'}),

                    # Description
                    html.Div([
                        html.Label('Description (Optional)'),
                        dcc.Textarea(
                            id='trip-description-input',
                            placeholder='Add notes about your trip...',
                            style={'width': '100%', 'padding': '0.75rem', 'borderRadius': '8px', 'border': '1px solid #ddd', 'minHeight': '80px'}
                        )
                    ])
                ], style={
                    'backgroundColor': '#FFFFFF',
                    'padding': '2rem',
                    'borderRadius': '12px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '2rem'
                }),

                # Bottom Section: Two-Column Layout
                html.Div([
                    # LEFT COLUMN: Draggable Favorites Panel
                    html.Div([
                        html.H3('Your Favorites', style={'color': '#003580', 'marginBottom': '1rem'}),

                        # Category Tabs
                        dcc.Tabs(
                            id='favorites-category-tabs',
                            value='all',
                            children=[
                                dcc.Tab(label='All', value='all'),
                                dcc.Tab(label='Restaurants', value='restaurant'),
                                dcc.Tab(label='Hotels', value='hotel'),
                                dcc.Tab(label='Attractions', value='attraction')
                            ]
                        ),

                        # Favorites List (will be populated by callback)
                        html.Div(id='draggable-favorites-list', style={'marginTop': '1rem', 'maxHeight': '600px', 'overflowY': 'auto'})

                    ], style={
                        'flex': '0 0 40%',
                        'backgroundColor': '#FFFFFF',
                        'padding': '1.5rem',
                        'borderRadius': '12px',
                        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                        'marginRight': '1rem'
                    }),

                    # RIGHT COLUMN: Timeline with Drop Zones
                    html.Div([
                        html.H3('Trip Schedule', style={'color': '#003580', 'marginBottom': '1rem'}),
                        html.P('Drag places from the left to organize your itinerary', style={'color': '#888', 'fontSize': '0.9rem', 'marginBottom': '1rem'}),

                        # Timeline (will be populated by callback based on dates)
                        html.Div(id='trip-timeline', style={'minHeight': '400px'})

                    ], style={
                        'flex': '0 0 58%',
                        'backgroundColor': '#FFFFFF',
                        'padding': '1.5rem',
                        'borderRadius': '12px',
                        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
                    })

                ], style={'display': 'flex', 'marginBottom': '2rem'}),

                # Save Button
                html.Div([
                    html.Button([
                        html.I(className='fas fa-save', style={'marginRight': '8px'}),
                        'Save Trip'
                    ], id='save-trip-btn', style={
                        'backgroundColor': '#deb522',
                        'color': '#FFFFFF',
                        'border': 'none',
                        'padding': '1rem 2rem',
                        'borderRadius': '8px',
                        'fontSize': '1.1rem',
                        'fontWeight': '600',
                        'cursor': 'pointer'
                    })
                ], style={'textAlign': 'center'})

            ], style={'maxWidth': '1400px', 'margin': '0 auto'})
        ], style={'padding': '2rem', 'backgroundColor': '#F2F6FA', 'minHeight': '100vh'})
    ])
