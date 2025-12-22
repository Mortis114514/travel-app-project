"""
Complete new Create Trip layout with drag-and-drop functionality
This will replace the current create_trip_layout in app.py
"""

from dash import html, dcc
from datetime import datetime, timedelta

def create_draggable_favorite_item(fav):
    """Create a draggable favorite item with grip handle"""
    icon_map = {
        'restaurant': 'fas fa-utensils',
        'hotel': 'fas fa-hotel',
        'attraction': 'fas fa-map-marker-alt'
    }

    return html.Div([
        html.Div([
            html.I(className=icon_map.get(fav['item_type'], 'fas fa-map-pin'),
                   style={'marginRight': '0.75rem', 'color': '#deb522', 'fontSize': '1.1rem'}),
            html.Div([
                html.Div(fav['item_name'], style={'fontWeight': '500', 'color': '#003580', 'fontSize': '0.95rem'}),
                html.Div(fav['item_type'].capitalize(), style={'fontSize': '0.8rem', 'color': '#888'})
            ], style={'flex': '1'}),
            html.I(className='fas fa-grip-vertical', style={'color': '#ccc'})
        ], style={'display': 'flex', 'alignItems': 'center', 'width': '100%'})
    ],
    id={'type': 'draggable-fav', 'item-type': fav['item_type'], 'item-id': fav['item_id']},
    draggable='true',
    **{
        'data-item-type': fav['item_type'],
        'data-item-id': str(fav['item_id']),
        'data-item-name': fav['item_name']
    },
    style={
        'padding': '0.75rem',
        'marginBottom': '0.5rem',
        'backgroundColor': '#F8F9FA',
        'border': '2px solid #E8ECEF',
        'borderRadius': '8px',
        'cursor': 'grab',
        'transition': 'all 0.2s ease',
        'userSelect': 'none'
    },
    className='draggable-item')


def create_day_drop_zone(day_number, items_for_day=[]):
    """Create a drop zone for a specific day with items"""

    # Create item cards for this day
    item_elements = []
    for item in items_for_day:
        icon_map = {
            'restaurant': 'fas fa-utensils',
            'hotel': 'fas fa-hotel',
            'attraction': 'fas fa-map-marker-alt'
        }

        item_card = html.Div([
            html.Div([
                html.I(className=icon_map.get(item['item_type'], 'fas fa-map-pin'),
                       style={'marginRight': '0.75rem', 'color': '#deb522'}),
                html.Div(item['item_name'], style={'flex': '1', 'fontWeight': '500', 'color': '#003580'}),
                html.Button(
                    html.I(className='fas fa-times'),
                    id={'type': 'remove-from-schedule', 'day': day_number, 'item-id': item['item_id'], 'item-type': item['item_type']},
                    style={
                        'backgroundColor': 'transparent',
                        'border': 'none',
                        'color': '#dc3545',
                        'cursor': 'pointer',
                        'padding': '0.25rem 0.5rem'
                    }
                )
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={
            'padding': '0.75rem',
            'marginBottom': '0.5rem',
            'backgroundColor': '#F0F8FF',
            'border': '1px solid #B8D4E8',
            'borderRadius': '6px'
        })
        item_elements.append(item_card)

    # Empty state
    if not item_elements:
        item_elements = [html.Div(
            'Drop places here',
            style={
                'padding': '2rem',
                'textAlign': 'center',
                'color': '#ccc',
                'fontStyle': 'italic',
                'border': '2px dashed #E0E0E0',
                'borderRadius': '8px'
            }
        )]

    return html.Div([
        html.Div(f'Day {day_number}', style={
            'fontWeight': '600',
            'color': '#003580',
            'marginBottom': '0.75rem',
            'fontSize': '1.1rem'
        }),
        html.Div(
            item_elements,
            id={'type': 'day-drop-zone', 'day': day_number},
            **{'data-day': str(day_number)},
            style={
                'minHeight': '120px',
                'padding': '0.75rem',
                'backgroundColor': '#FAFBFC',
                'borderRadius': '8px',
                'border': '2px dashed #D0D5DD'
            },
            className='drop-zone'
        )
    ], style={'marginBottom': '1.5rem'})


def create_trip_layout(session_data=None):
    """
    New Create Trip layout with drag-and-drop interface

    Structure:
    - Top: Trip information form
    - Bottom: Two-column layout
      - Left (40%): Draggable favorites categorized
      - Right (60%): Timeline with drop zones for each day
    - Bottom: Save button
    """
    from utils.favorites import get_user_favorites
    from utils.auth import get_session

    # Get user's favorites
    user_id = None
    if session_data and 'session_id' in session_data:
        user_id = get_session(session_data['session_id'])

    return html.Div([
        # Header
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
                'maxWidth': '1600px',
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

                    html.Div([
                        # Trip Name
                        html.Div([
                            html.Label('Trip Name *', style={'fontWeight': '500', 'marginBottom': '0.5rem', 'display': 'block'}),
                            dcc.Input(
                                id='trip-name-input',
                                type='text',
                                placeholder='e.g., Kyoto Summer Adventure 2024',
                                style={
                                    'width': '100%',
                                    'padding': '0.75rem',
                                    'borderRadius': '8px',
                                    'border': '1px solid #ddd',
                                    'fontSize': '1rem'
                                }
                            )
                        ], style={'flex': '2', 'marginRight': '1rem'}),

                        # Start Date
                        html.Div([
                            html.Label('Start Date *', style={'fontWeight': '500', 'marginBottom': '0.5rem', 'display': 'block'}),
                            dcc.DatePickerSingle(
                                id='trip-start-date',
                                placeholder='Start date',
                                display_format='YYYY-MM-DD',
                                style={'width': '100%'}
                            )
                        ], style={'flex': '1', 'marginRight': '1rem'}),

                        # End Date
                        html.Div([
                            html.Label('End Date *', style={'fontWeight': '500', 'marginBottom': '0.5rem', 'display': 'block'}),
                            dcc.DatePickerSingle(
                                id='trip-end-date',
                                placeholder='End date',
                                display_format='YYYY-MM-DD',
                                style={'width': '100%'}
                            )
                        ], style={'flex': '1'})
                    ], style={'display': 'flex', 'marginBottom': '1rem'}),

                    # Description
                    html.Div([
                        html.Label('Description (Optional)', style={'fontWeight': '500', 'marginBottom': '0.5rem', 'display': 'block'}),
                        dcc.Textarea(
                            id='trip-description-input',
                            placeholder='Add any notes or details about your trip...',
                            style={
                                'width': '100%',
                                'padding': '0.75rem',
                                'borderRadius': '8px',
                                'border': '1px solid #ddd',
                                'fontSize': '1rem',
                                'minHeight': '80px',
                                'resize': 'vertical'
                            }
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
                        html.H3('Your Favorites', style={
                            'color': '#003580',
                            'fontSize': '1.3rem',
                            'marginBottom': '1rem'
                        }),
                        html.P('Drag places to your itinerary on the right', style={
                            'color': '#888',
                            'fontSize': '0.9rem',
                            'marginBottom': '1rem'
                        }),

                        # Category filter
                        html.Div([
                            html.Button('All', id={'type': 'fav-filter', 'category': 'all'},
                                      className='filter-chip active-filter', n_clicks=0),
                            html.Button('Restaurants', id={'type': 'fav-filter', 'category': 'restaurant'},
                                      className='filter-chip', n_clicks=0),
                            html.Button('Hotels', id={'type': 'fav-filter', 'category': 'hotel'},
                                      className='filter-chip', n_clicks=0),
                            html.Button('Attractions', id={'type': 'fav-filter', 'category': 'attraction'},
                                      className='filter-chip', n_clicks=0)
                        ], style={'marginBottom': '1rem', 'display': 'flex', 'gap': '0.5rem', 'flexWrap': 'wrap'}),

                        # Favorites list (populated by callback)
                        html.Div(
                            id='draggable-favorites-container',
                            style={
                                'maxHeight': '600px',
                                'overflowY': 'auto',
                                'overflowX': 'hidden'
                            }
                        )

                    ], style={
                        'flex': '0 0 38%',
                        'backgroundColor': '#FFFFFF',
                        'padding': '1.5rem',
                        'borderRadius': '12px',
                        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                        'marginRight': '2%'
                    }),

                    # RIGHT COLUMN: Timeline with Drop Zones
                    html.Div([
                        html.H3('Trip Schedule', style={
                            'color': '#003580',
                            'fontSize': '1.3rem',
                            'marginBottom': '1rem'
                        }),

                        # Timeline container (populated by callback based on dates)
                        html.Div(
                            id='trip-timeline-container',
                            style={
                                'maxHeight': '600px',
                                'overflowY': 'auto'
                            }
                        )

                    ], style={
                        'flex': '0 0 60%',
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
                    ], id='save-trip-btn', n_clicks=0, style={
                        'backgroundColor': '#deb522',
                        'color': '#FFFFFF',
                        'border': 'none',
                        'padding': '1rem 2.5rem',
                        'borderRadius': '8px',
                        'fontSize': '1.1rem',
                        'fontWeight': '600',
                        'cursor': 'pointer',
                        'boxShadow': '0 4px 12px rgba(222, 181, 34, 0.4)',
                        'transition': 'all 0.3s ease'
                    })
                ], style={'textAlign': 'center'})

            ], style={'maxWidth': '1600px', 'margin': '0 auto'})
        ], style={'padding': '2rem', 'backgroundColor': '#F2F6FA', 'minHeight': '100vh'}),

        # Hidden store for tracking items in schedule
        dcc.Store(id='trip-schedule-items', data={})
    ])
