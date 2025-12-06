
import dash
from dash import dcc, html, Input, Output, callback
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# --- Data Loading and Preprocessing ---
def load_and_prepare_data():
    """
    Loads hotel and review data, merges them, and generates random review dates.
    This is a temporary solution as the original dataset does not have timestamps.
    """
    try:
        hotels_df = pd.read_csv('data/Hotels.csv')
        reviews_df = pd.read_csv('data/HotelReviews.csv')
    except FileNotFoundError:
        return pd.DataFrame()

    # --- Temporary: Generate random dates for reviews ---
    # Create a date range for the last 2 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    # Generate random dates
    num_reviews = len(reviews_df)
    random_dates = [start_date + timedelta(seconds=np.random.randint(0, int((end_date - start_date).total_seconds()))) for _ in range(num_reviews)]
    
    reviews_df['Review_Date'] = pd.to_datetime(random_dates)
    # --- End of temporary solution ---

    # Merge dataframes
    df = pd.merge(reviews_df, hotels_df, on='Hotel_ID')
    
    # Ensure correct data types
    df['Review_Rating'] = pd.to_numeric(df['Review_Rating'], errors='coerce')
    df.dropna(subset=['Review_Rating', 'Review_Date', 'HotelName'], inplace=True)
    
    return df

# --- UI Components ---
def create_analytics_layout(df):
    """
    Creates the layout for the analytics page.
    """
    if df.empty:
        return html.Div("Data could not be loaded. Please check the data files.", style={'color': 'red', 'textAlign': 'center'})

    hotel_options = [{'label': hotel, 'value': hotel} for hotel in sorted(df['HotelName'].unique())]
    
    return html.Div([
        # Header
        html.Div([
            html.A('← Back to Main Page', href='/', style={
                'position': 'absolute',
                'top': '1rem',
                'left': '1rem',
                'color': '#deb522',
                'textDecoration': 'none',
                'fontWeight': 'bold',
                'fontSize': '1rem'
            }),
            html.H1('Hotel Review Analytics', style={'color': '#deb522'}),
            html.P('Analyze hotel ratings over time and their distribution.', style={'color': '#cccccc'})
        ], style={'textAlign': 'center', 'marginBottom': '2rem', 'position': 'relative'}),

        # Controls
        html.Div([
            dcc.Dropdown(
                id='analytics-hotel-dropdown',
                options=hotel_options,
                placeholder='Select a Hotel (optional)',
                style={'flex': '1', 'marginRight': '1rem'}
            ),
            dcc.DatePickerRange(
                id='analytics-date-picker',
                min_date_allowed=df['Review_Date'].min().date(),
                max_date_allowed=df['Review_Date'].max().date(),
                start_date=df['Review_Date'].min().date(),
                end_date=df['Review_Date'].max().date(),
                display_format='YYYY-MM-DD',
                style={'border': '1px solid #333'}
            )
        ], style={'display': 'flex', 'maxWidth': '1000px', 'margin': '0 auto 2rem auto'}),
        
        # Charts
        html.Div([
            dcc.Graph(id='rating-distribution-chart'),
            dcc.Graph(id='rating-over-time-chart')
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '2rem', 'maxWidth': '1600px', 'margin': '0 auto'})
    ], style={'padding': '2rem', 'backgroundColor': '#0a0a0a'})

# --- Callbacks ---
def register_analytics_callbacks(app, df):
    """
    Registers the callbacks for the analytics page.
    """
    if df.empty:
        return

    @app.callback(
        [Output('rating-distribution-chart', 'figure'),
         Output('rating-over-time-chart', 'figure')],
        [Input('analytics-hotel-dropdown', 'value'),
         Input('analytics-date-picker', 'start_date'),
         Input('analytics-date-picker', 'end_date')]
    )
    def update_charts(selected_hotel, start_date, end_date):
        filtered_df = df.copy()

        # Filter by date
        filtered_df = filtered_df[(filtered_df['Review_Date'] >= pd.to_datetime(start_date)) & (filtered_df['Review_Date'] <= pd.to_datetime(end_date))]

        # Filter by hotel
        if selected_hotel:
            filtered_df = filtered_df[filtered_df['HotelName'] == selected_hotel]

        # --- Create charts ---
        if not filtered_df.empty:
            # --- Create Rating Distribution Chart ---
            rating_counts = filtered_df['Review_Rating'].value_counts().sort_index()
            dist_fig = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                labels={'x': 'Rating', 'y': 'Number of Reviews'},
                title=f'Rating Distribution for {selected_hotel or "All Hotels"}'
            )

            # --- Create Rating Over Time Chart ---
            time_df = filtered_df.sort_values('Review_Date')
            time_df['rolling_avg'] = time_df['Review_Rating'].rolling(window=30, min_periods=1).mean()
            
            time_fig = px.line(
                time_df,
                x='Review_Date',
                y='rolling_avg',
                title=f'30-Day Rolling Average Rating for {selected_hotel or "All Hotels"}'
            )
        else:
            # Create empty charts if no data
            dist_fig = px.bar(title=f'No data to display for {selected_hotel or "All Hotels"}')
            time_fig = px.line(title=f'No data to display for {selected_hotel or "All Hotels"}')

        dist_fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='#1a1a1a',
            font_color='#ffffff',
            title_font_color='#deb522'
        )

        time_fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='#1a1a1a',
            font_color='#ffffff',
            title_font_color='#deb522',
            xaxis_title='Date',
            yaxis_title='Average Rating'
        )

        return dist_fig, time_fig
