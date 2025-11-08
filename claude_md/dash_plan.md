# Restaurant Detail Page - Dash Architecture Blueprint

## Overview

This blueprint defines the architecture for adding a comprehensive restaurant detail page feature to the Voyage restaurant discovery application. Users will be able to click on any restaurant card to navigate to a dedicated detail page with full information, accessible via URL routing (e.g., `/restaurant/123`). The feature maintains the existing dark theme with gold accent (#deb522) and integrates seamlessly with the current authentication and navigation systems.

## Requirements Analysis

### Functional Requirements
- **Clickable Restaurant Cards**: All restaurant cards (home page and list page) should be clickable and navigate to detail page
- **URL-based Routing**: Each restaurant should have a unique URL route based on Restaurant_ID
- **Comprehensive Information Display**: Show all available restaurant data including ratings, pricing, location, categories
- **Back Navigation**: Easy return to previous page (home or restaurant list)
- **Responsive Layout**: Detail page should work on all screen sizes
- **Session Persistence**: Maintain user authentication during navigation

### Data Requirements
- **Primary Data Source**: `restaurants` table in SQLite database (`./data/restaurants.db`)
- **Data Access**: Use existing `get_restaurant_by_id(restaurant_id)` function from `utils/database.py`
- **Available Fields**:
  - Restaurant_ID (primary key)
  - Name, JapaneseName
  - Station, Lat, Long
  - FirstCategory, SecondCategory
  - TotalRating, DinnerRating, LunchRating
  - DinnerPrice, LunchPrice, Price_Category
  - ReviewNum, Rating_Category
- **Optional Enhancement**: Reviews data (if `reviews` table exists in database)

### UI/UX Requirements
- **Visual Hierarchy**: Clear separation of information sections
- **Rating Display**: Prominent display of overall rating with star visualization
- **Price Information**: Clear presentation of dinner and lunch pricing
- **Location Information**: Station name with potential map integration placeholder
- **Category Tags**: Visual tags for cuisine categories
- **Loading State**: Show loading indicator while fetching data
- **Error Handling**: Display friendly error message if restaurant not found
- **Back Button**: Clear navigation back to previous view

### Integration Points
- **Existing Card Components**: Modify `create_destination_card()` to include click functionality
- **Restaurant List Grid**: Modify restaurant list cards to include click functionality
- **URL Routing**: Extend existing `display_page()` callback to handle restaurant detail routes
- **Database Module**: Use existing `get_restaurant_by_id()` function (no changes needed)
- **Authentication**: Ensure detail page respects session authentication
- **Navigation State**: Track previous page for proper back navigation

## Layout Design

### Component Hierarchy

```
html.Div (page-content)
└── html.Div (restaurant-detail-page) [when URL matches /restaurant/{id}]
    ├── html.Div (detail-header-section)
    │   ├── html.Div (header-content-wrapper)
    │   │   ├── html.Button (back-button) [id: restaurant-detail-back-btn]
    │   │   └── html.Div (user-avatar-section)
    │   │       ├── html.Div (user-avatar) [id: user-avatar-detail]
    │   │       └── html.Div (user-dropdown) [id: user-dropdown-detail]
    │   └── dcc.Store (dropdown-open-detail)
    │
    ├── html.Div (detail-hero-section)
    │   ├── html.Img (restaurant-hero-image)
    │   ├── html.Div (hero-overlay)
    │   └── html.Div (hero-content)
    │       ├── html.H1 (restaurant-name)
    │       ├── html.Div (japanese-name)
    │       ├── html.Div (rating-display-large)
    │       │   ├── html.Span (star-icons × 5)
    │       │   └── html.Span (rating-number)
    │       └── html.Div (quick-info-chips)
    │           ├── html.Span (category-chip)
    │           ├── html.Span (price-category-chip)
    │           └── html.Span (review-count-chip)
    │
    ├── html.Div (detail-main-content)
    │   ├── html.Div (content-left-column)
    │   │   ├── html.Div (info-section-location)
    │   │   │   ├── html.H3 (section-title: "Location")
    │   │   │   ├── html.Div (station-info)
    │   │   │   │   ├── html.I (map-marker-icon)
    │   │   │   │   └── html.Span (station-name)
    │   │   │   └── html.Div (coordinates-info) [if Lat/Long available]
    │   │   │       └── html.Small (lat/long display)
    │   │   │
    │   │   ├── html.Div (info-section-pricing)
    │   │   │   ├── html.H3 (section-title: "Pricing")
    │   │   │   ├── html.Div (price-item-dinner)
    │   │   │   │   ├── html.I (moon-icon)
    │   │   │   │   ├── html.Span (label: "Dinner")
    │   │   │   │   └── html.Span (price-value)
    │   │   │   └── html.Div (price-item-lunch)
    │   │   │       ├── html.I (sun-icon)
    │   │   │       ├── html.Span (label: "Lunch")
    │   │   │       └── html.Span (price-value)
    │   │   │
    │   │   ├── html.Div (info-section-categories)
    │   │   │   ├── html.H3 (section-title: "Categories")
    │   │   │   └── html.Div (category-tags-container)
    │   │   │       ├── html.Span (category-tag-1)
    │   │   │       └── html.Span (category-tag-2)
    │   │   │
    │   │   └── html.Div (info-section-map-placeholder)
    │   │       ├── html.H3 (section-title: "Map")
    │   │       └── html.Div (map-placeholder-content)
    │   │           ├── html.I (map-icon)
    │   │           └── html.P (map-coming-soon-text)
    │   │
    │   └── html.Div (content-right-column)
    │       ├── html.Div (ratings-breakdown-section)
    │       │   ├── html.H3 (section-title: "Ratings Breakdown")
    │       │   ├── html.Div (rating-item-total)
    │       │   │   ├── html.Span (rating-label: "Overall")
    │       │   │   ├── html.Div (rating-stars)
    │       │   │   └── html.Span (rating-value)
    │       │   ├── html.Div (rating-item-dinner)
    │       │   │   ├── html.Span (rating-label: "Dinner")
    │       │   │   ├── html.Div (rating-stars)
    │       │   │   └── html.Span (rating-value)
    │       │   └── html.Div (rating-item-lunch)
    │       │       ├── html.Span (rating-label: "Lunch")
    │       │       ├── html.Div (rating-stars)
    │       │       └── html.Span (rating-value)
    │       │
    │       ├── html.Div (statistics-section)
    │       │   ├── html.H3 (section-title: "Statistics")
    │       │   ├── html.Div (stat-item-reviews)
    │       │   │   ├── html.I (comment-icon)
    │       │   │   ├── html.Span (stat-value)
    │       │   │   └── html.Span (stat-label)
    │       │   └── html.Div (stat-item-category)
    │       │       ├── html.I (award-icon)
    │       │       ├── html.Span (stat-value)
    │       │       └── html.Span (stat-label)
    │       │
    │       └── html.Div (reviews-section-placeholder)
    │           ├── html.H3 (section-title: "Reviews")
    │           └── html.Div (reviews-coming-soon)
    │               ├── html.I (comments-icon)
    │               └── html.P (reviews-placeholder-text)
    │
    └── dcc.Store (restaurant-detail-data) [storage_type: 'memory']
```

### Component Specifications

#### 1. Detail Header Section
- **Component**: `html.Div` with class `detail-header-section`
- **Props**:
  - style: `{'backgroundColor': '#1a1a1a', 'borderBottom': '1px solid #333', 'position': 'sticky', 'top': '0', 'zIndex': '1000'}`
- **CSS Classes**: `detail-header-section` (new class needed)
- **Data Binding**: None (static structure)
- **Children**:
  - Back button (Bootstrap-style with Font Awesome arrow-left icon)
  - User avatar dropdown (reuse existing pattern)

#### 2. Detail Hero Section
- **Component**: `html.Div` with class `detail-hero-section`
- **Props**:
  - style: `{'position': 'relative', 'height': '50vh', 'minHeight': '400px', 'overflow': 'hidden'}`
- **CSS Classes**: `detail-hero-section` (new class, similar to hero-section)
- **Data Binding**: Restaurant name, Japanese name, TotalRating from restaurant data
- **Image Source**: `/assets/Hazuki.jpg` (placeholder, same as current cards)
- **Styling Notes**:
  - Use dark overlay gradient (bottom to top)
  - Gold accent for rating display
  - White text for restaurant name
  - Gray text for Japanese name

#### 3. Main Content Section (Two-Column Layout)
- **Component**: `html.Div` with class `detail-main-content`
- **Props**:
  - style: `{'maxWidth': '1400px', 'margin': '0 auto', 'padding': '3rem 2rem', 'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '3rem'}`
- **CSS Classes**: `detail-main-content`, `content-left-column`, `content-right-column`
- **Data Binding**: All restaurant fields
- **Responsive Behavior**: Stack to single column on screens < 768px

#### 4. Information Sections (Left Column)
Each section follows this pattern:
- **Container**: `html.Div` with class `info-section`
- **Title**: `html.H3` with class `section-title` (color: #deb522)
- **Content**: Varies by section
- **Styling**: Dark card background (#1a1a1a), rounded corners, border (#333)

**Location Section**:
- Display: Station name with map marker icon
- Additional: Lat/Long if available (small gray text)

**Pricing Section**:
- Display: Two rows (Dinner and Lunch)
- Icons: Moon (fa-moon) for dinner, Sun (fa-sun) for lunch
- Format: Currency symbol with price value
- Handle NULL: Show "Not Available" in gray

**Categories Section**:
- Display: Pills/badges for FirstCategory and SecondCategory
- Styling: Gold border, transparent background with gold text

**Map Placeholder Section**:
- Display: Icon and "Map integration coming soon" text
- Future Enhancement: Integrate actual map with Lat/Long

#### 5. Information Sections (Right Column)

**Ratings Breakdown**:
- Display: Three rows (Overall, Dinner, Lunch)
- Each row: Label, star icons, numeric value
- Star Display: Full stars (gold) for whole numbers, empty stars (gray) for remainder
- Styling: Larger overall rating, smaller dinner/lunch

**Statistics Section**:
- Display: Review count, Rating category
- Icons: Comment icon for reviews, Award icon for category
- Styling: Large number, small label below

**Reviews Placeholder**:
- Display: "Reviews integration coming soon"
- Future Enhancement: Fetch and display actual reviews from reviews table

#### 6. Loading State Component
- **Component**: `html.Div` with class `loading-container`
- **Display**: When restaurant data is being fetched
- **Content**:
  - Spinner icon (fa-spinner fa-spin)
  - "Loading restaurant details..." text
- **Styling**: Centered, full height, dark background

#### 7. Error State Component
- **Component**: `html.Div` with class `error-container`
- **Display**: When restaurant not found or error occurs
- **Content**:
  - Error icon (fa-exclamation-triangle)
  - "Restaurant not found" heading
  - Descriptive message
  - Back button
- **Styling**: Centered, red/gold color scheme

### State Management

#### dcc.Store Components

**1. restaurant-detail-data**
- **Purpose**: Store fetched restaurant data for the current detail page
- **Storage Type**: `'memory'` (cleared on page refresh)
- **Data Structure**:
```python
{
    'Restaurant_ID': int,
    'Name': str,
    'JapaneseName': str,
    'Station': str,
    'FirstCategory': str,
    'SecondCategory': str,
    'TotalRating': float,
    'DinnerRating': float,
    'LunchRating': float,
    'DinnerPrice': str,
    'LunchPrice': str,
    'Price_Category': str,
    'ReviewNum': int,
    'Rating_Category': str,
    'Lat': float,
    'Long': float
}
```

**2. previous-page-location** (NEW)
- **Purpose**: Track the previous page URL for proper back navigation
- **Storage Type**: `'memory'`
- **Data Structure**: `{'from': str}` (e.g., `{'from': 'home'}` or `{'from': 'restaurant-list'}`)

**3. selected-restaurant-id** (NEW)
- **Purpose**: Store the restaurant ID when user clicks a card
- **Storage Type**: `'memory'`
- **Data Structure**: `{'id': int}`

### CSS Styling Requirements

**New CSS Classes Needed** (add to `voyage_styles.css`):

```css
/* Restaurant Detail Page Styles */

.detail-header-section {
    /* Sticky header for detail page */
    /* Similar to restaurant list header */
}

.detail-hero-section {
    /* Hero section for restaurant image */
    /* Similar to existing hero-section but shorter */
}

.detail-main-content {
    /* Two-column grid layout */
}

.content-left-column, .content-right-column {
    /* Column styling */
}

.info-section {
    /* Card styling for each information section */
    /* Dark background, gold border, rounded corners */
}

.section-title {
    /* Section headings */
    /* Gold color, bold, larger font */
}

.rating-display-large {
    /* Large rating display in hero */
}

.rating-item {
    /* Individual rating rows in breakdown */
}

.stat-item {
    /* Statistics display items */
}

.category-tag {
    /* Cuisine category pills */
}

.price-item {
    /* Price display rows */
}

.loading-container, .error-container {
    /* Loading and error state styling */
}
```

## Callback Architecture

### Callback Dependency Graph

```
URL Change (pathname)
    │
    ├──> [Callback 1: Route Detector]
    │       │
    │       └──> Outputs: selected-restaurant-id, previous-page-location
    │               │
    │               └──> Triggers ↓
    │
    ├──> [Callback 2: Page Router (MODIFIED display_page)]
    │       │
    │       └──> Checks pathname:
    │               - /restaurant/{id} → create_restaurant_detail_page()
    │               - /restaurant-list → create_restaurant_list_page()
    │               - / → create_main_layout()
    │               - else → login page
    │
    └──> [Callback 3: Detail Page Data Loader]
            │
            └──> Inputs: selected-restaurant-id
            └──> Outputs: restaurant-detail-data
                    │
                    └──> Triggers ↓

[Callback 4: Detail Page Content Renderer]
    │
    └──> Inputs: restaurant-detail-data
    └──> Outputs: detail-page-content
            │
            └──> Returns: Populated layout or loading/error state


[Callback 5: Restaurant Card Click Handler]
    │
    └──> Inputs: Click events from restaurant cards (ALL pattern)
    └──> Outputs: url.pathname (navigation trigger)


[Callback 6: Back Button Handler]
    │
    └──> Inputs: restaurant-detail-back-btn click
    └──> State: previous-page-location
    └──> Outputs: url.pathname (navigate back)


[Callback 7: User Dropdown Toggle (Detail Page)]
    │
    └──> Inputs: user-avatar-detail click
    └──> Outputs: user-dropdown-detail className, dropdown-open-detail


[Callback 8: Logout from Detail Page]
    │
    └──> Inputs: menu-logout-detail click
    └──> Outputs: session-store (clear session)
```

### Callback Specifications

#### Callback 1: Route Detector

**Purpose**: Parse URL pathname to extract restaurant ID and track navigation context

**Inputs**:
- `Input('url', 'pathname')`: URL pathname change

**Outputs**:
- `Output('selected-restaurant-id', 'data')`: Restaurant ID extracted from URL
- `Output('previous-page-location', 'data')`: Previous page context

**State**: None

**Logic**:
```python
def detect_restaurant_route(pathname):
    """
    Parse URL pathname to extract restaurant ID

    Examples:
        /restaurant/123 → {'id': 123}
        /restaurant-list → {'id': None}
        / → {'id': None}
    """
    if pathname and pathname.startswith('/restaurant/'):
        try:
            # Extract ID from URL
            restaurant_id = int(pathname.split('/')[-1])
            return {'id': restaurant_id}, {'from': 'restaurant-list'}
        except (ValueError, IndexError):
            # Invalid restaurant ID
            return {'id': None}, {'from': 'home'}
    elif pathname == '/restaurant-list':
        return {'id': None}, {'from': 'home'}
    else:
        return {'id': None}, {'from': 'home'}
```

**Error Handling**:
- Invalid restaurant ID in URL → return None, log warning
- Non-numeric ID → return None, show error page

**Performance Notes**:
- Simple string parsing, no database query
- Use `prevent_initial_call=False` to handle direct URL access

---

#### Callback 2: Page Router (MODIFIED)

**Purpose**: Extend existing `display_page()` callback to handle restaurant detail routes

**Inputs**:
- `Input('url', 'pathname')`: URL pathname change
- `Input('session-store', 'data')`: Current session data
- `Input('page-mode', 'data')`: Current page mode
- `Input('view-mode', 'data')`: Current view mode
- `Input('selected-restaurant-id', 'data')`: Restaurant ID from route detector (NEW)

**Outputs**:
- `Output('page-content', 'children')`: Page content
- `Output('page-mode', 'data')`: Page mode

**State**: None

**Logic**:
```python
def display_page(pathname, session_data, current_mode, view_mode, restaurant_id_data):
    """
    Route user to appropriate page based on pathname and authentication

    Priority:
    1. Check authentication (redirect to login if not authenticated)
    2. Check for restaurant detail route (/restaurant/{id})
    3. Check for restaurant list route (/restaurant-list or view-mode)
    4. Default to home page
    """
    # Step 1: Clean expired sessions
    clean_expired_sessions()

    # Step 2: Validate session
    if session_data and 'session_id' in session_data:
        user_id = get_session(session_data['session_id'])

        if user_id:
            # User is authenticated

            # Check for restaurant detail route
            if pathname and pathname.startswith('/restaurant/'):
                if restaurant_id_data and restaurant_id_data.get('id'):
                    return create_restaurant_detail_page(restaurant_id_data['id']), 'main'
                else:
                    # Invalid restaurant ID, redirect to list
                    return create_restaurant_list_page(), 'main'

            # Check for restaurant list route
            elif view_mode == 'restaurant-list' or pathname == '/restaurant-list':
                return create_restaurant_list_page(), 'main'

            # Default to home page
            else:
                return create_main_layout(), 'main'

    # User not authenticated, show login/register
    if current_mode == 'register':
        return create_register_layout(), 'register'

    return create_login_layout(), 'login'
```

**Integration Notes**:
- Modify existing `display_page()` callback in app.py (lines 748-776)
- Add new input for `selected-restaurant-id`
- Add new route check before existing view-mode checks

**Error Handling**:
- Invalid restaurant ID → redirect to restaurant list with error message (use dcc.Store for flash messages)
- Database connection error → show error page with retry button
- Missing session → redirect to login

**Performance Notes**:
- No database query in this callback (just routing logic)
- Restaurant data fetching happens in separate callback

---

#### Callback 3: Detail Page Data Loader

**Purpose**: Fetch restaurant data from database when restaurant ID changes

**Inputs**:
- `Input('selected-restaurant-id', 'data')`: Restaurant ID to fetch

**Outputs**:
- `Output('restaurant-detail-data', 'data')`: Fetched restaurant data

**State**: None

**Logic**:
```python
def load_restaurant_detail(restaurant_id_data):
    """
    Fetch restaurant data from database

    Returns:
        dict: Restaurant data or None if not found
    """
    if not restaurant_id_data or not restaurant_id_data.get('id'):
        raise PreventUpdate

    restaurant_id = restaurant_id_data['id']

    try:
        # Fetch from database using existing function
        restaurant_data = get_restaurant_by_id(restaurant_id)

        if restaurant_data:
            return restaurant_data
        else:
            # Restaurant not found
            return {'error': 'Restaurant not found', 'id': restaurant_id}

    except Exception as e:
        # Database error
        return {'error': str(e), 'id': restaurant_id}
```

**Error Handling**:
- Restaurant not found → return error dict with flag
- Database connection error → return error dict with message
- Invalid ID type → raise PreventUpdate

**Performance Notes**:
- Single database query using indexed Restaurant_ID
- Fast lookup (< 10ms typical)
- Use `prevent_initial_call=True` to avoid unnecessary query on page load

---

#### Callback 4: Detail Page Content Renderer

**Purpose**: Render detail page layout with fetched restaurant data

**Inputs**:
- `Input('restaurant-detail-data', 'data')`: Restaurant data

**Outputs**:
- `Output('page-content', 'children')`: Rendered detail page (ALTERNATIVE: use separate container ID)

**State**: None

**Logic**:
```python
def render_restaurant_detail(restaurant_data):
    """
    Render restaurant detail page with data

    Returns:
        html.Div: Complete detail page layout or loading/error state
    """
    if not restaurant_data:
        # Loading state
        return create_loading_state()

    if 'error' in restaurant_data:
        # Error state
        return create_error_state(restaurant_data['error'])

    # Render full detail page
    return create_detail_page_layout(restaurant_data)


def create_detail_page_layout(data):
    """
    Build complete detail page layout

    Structure:
    - Header with back button
    - Hero section with restaurant image and main info
    - Two-column content section
    - Left: Location, Pricing, Categories, Map
    - Right: Ratings breakdown, Statistics, Reviews
    """
    return html.Div([
        # Header
        create_detail_header(),

        # Hero
        create_detail_hero(data),

        # Main content
        html.Div([
            # Left column
            html.Div([
                create_location_section(data),
                create_pricing_section(data),
                create_categories_section(data),
                create_map_placeholder_section(data)
            ], className='content-left-column'),

            # Right column
            html.Div([
                create_ratings_breakdown_section(data),
                create_statistics_section(data),
                create_reviews_placeholder_section(data)
            ], className='content-right-column')
        ], className='detail-main-content')
    ], className='restaurant-detail-page')


def create_loading_state():
    """Loading spinner with message"""
    return html.Div([
        html.I(className='fas fa-spinner fa-spin',
               style={'fontSize': '3rem', 'color': '#deb522'}),
        html.P('Loading restaurant details...',
               style={'color': '#ffffff', 'marginTop': '1rem'})
    ], className='loading-container')


def create_error_state(error_message):
    """Error display with back button"""
    return html.Div([
        html.I(className='fas fa-exclamation-triangle',
               style={'fontSize': '3rem', 'color': '#deb522'}),
        html.H2('Restaurant Not Found',
                style={'color': '#ffffff', 'marginTop': '1rem'}),
        html.P(error_message,
               style={'color': '#888888', 'marginBottom': '2rem'}),
        html.Button([
            html.I(className='fas fa-arrow-left'),
            'Back to Restaurants'
        ], id='error-back-btn', className='btn-primary', n_clicks=0)
    ], className='error-container')
```

**Helper Functions** (to be created):
- `create_detail_header()`: Header with back button and user dropdown
- `create_detail_hero(data)`: Hero section with image and main info
- `create_location_section(data)`: Location information card
- `create_pricing_section(data)`: Pricing information card
- `create_categories_section(data)`: Category tags display
- `create_map_placeholder_section(data)`: Map placeholder
- `create_ratings_breakdown_section(data)`: Detailed ratings display
- `create_statistics_section(data)`: Review count and category stats
- `create_reviews_placeholder_section(data)`: Reviews placeholder

**Data Transformation Notes**:
- Handle NULL values for prices (show "Not Available")
- Format ratings to 1 decimal place
- Generate star icons based on rating value (full/empty stars)
- Format review count with commas (e.g., "1,234 reviews")

**Error Handling**:
- Missing required fields → use default values or "N/A"
- Invalid data types → log warning and use fallback

**Performance Notes**:
- Pure rendering logic, no database queries
- Use Python string formatting for clean code

---

#### Callback 5: Restaurant Card Click Handler

**Purpose**: Detect when user clicks a restaurant card and navigate to detail page

**Inputs**:
- `Input({'type': 'restaurant-card', 'index': ALL}, 'n_clicks')`: Click events from all restaurant cards

**Outputs**:
- `Output('url', 'pathname')`: Update URL to trigger navigation

**State**:
- `State({'type': 'restaurant-card', 'index': ALL}, 'id')`: Card IDs to extract restaurant IDs

**Logic**:
```python
def handle_card_click(n_clicks_list, card_ids):
    """
    Handle restaurant card clicks and navigate to detail page

    Uses pattern matching callback with ALL pattern
    to handle any number of restaurant cards
    """
    ctx = callback_context

    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    # Determine which card was clicked
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_dict = json.loads(triggered_id)
    restaurant_id = triggered_dict['index']

    # Navigate to detail page
    return f'/restaurant/{restaurant_id}'
```

**Integration Notes**:
- Requires modifying card creation functions to add pattern-matching IDs
- Update `create_destination_card()` to wrap in `html.Div` with ID
- Update restaurant list grid cards similarly

**Card Modification Example**:
```python
def create_destination_card(restaurant):
    """Modified to be clickable"""
    card_content = html.Div([
        # ... existing card content ...
    ], className='destination-card')

    # Wrap in clickable container with pattern-matching ID
    return html.Div(
        card_content,
        id={'type': 'restaurant-card', 'index': restaurant['Restaurant_ID']},
        n_clicks=0
    )
```

**Error Handling**:
- No clicked card detected → raise PreventUpdate
- Invalid restaurant ID → log error and raise PreventUpdate

**Performance Notes**:
- Lightweight callback, just URL update
- No database queries

---

#### Callback 6: Back Button Handler

**Purpose**: Navigate back to previous page when back button is clicked

**Inputs**:
- `Input('restaurant-detail-back-btn', 'n_clicks')`: Back button clicks

**Outputs**:
- `Output('url', 'pathname')`: Update URL to navigate back
- `Output('view-mode', 'data')`: Update view mode to match destination

**State**:
- `State('previous-page-location', 'data')`: Previous page context

**Logic**:
```python
def handle_back_button(n_clicks, previous_page):
    """
    Navigate back to previous page

    Routes:
    - from 'restaurant-list' → '/restaurant-list' (view-mode: 'restaurant-list')
    - from 'home' → '/' (view-mode: 'home')
    """
    if not n_clicks:
        raise PreventUpdate

    if previous_page and previous_page.get('from') == 'restaurant-list':
        return '/restaurant-list', 'restaurant-list'
    else:
        return '/', 'home'
```

**Error Handling**:
- Missing previous page data → default to home page

**Performance Notes**:
- Simple routing logic, no side effects

---

#### Callback 7: User Dropdown Toggle (Detail Page)

**Purpose**: Toggle user dropdown menu on detail page

**Inputs**:
- `Input('user-avatar-detail', 'n_clicks')`: Avatar clicks

**Outputs**:
- `Output('user-dropdown-detail', 'className')`: Dropdown visibility class
- `Output('dropdown-open-detail', 'data')`: Dropdown state

**State**:
- `State('dropdown-open-detail', 'data')`: Current dropdown state

**Logic**:
```python
def toggle_user_dropdown_detail(n_clicks, is_open):
    """
    Toggle user dropdown menu on detail page

    Identical logic to existing toggle_user_dropdown callback
    """
    if n_clicks:
        new_state = not is_open
        className = 'user-dropdown show' if new_state else 'user-dropdown'
        return className, new_state
    raise PreventUpdate
```

**Integration Notes**:
- Reuse existing dropdown styling
- Same dropdown menu items (Profile, Settings, Logout)

---

#### Callback 8: Logout from Detail Page

**Purpose**: Handle logout click from detail page dropdown menu

**Inputs**:
- `Input('menu-logout-detail', 'n_clicks')`: Logout menu item clicks

**Outputs**:
- `Output('session-store', 'data')`: Clear session data

**State**:
- `State('session-store', 'data')`: Current session data

**Logic**:
```python
def logout_from_detail_page(n_clicks, session_data):
    """
    Handle logout from detail page

    Identical logic to existing logout callbacks
    """
    if not n_clicks:
        raise PreventUpdate

    if session_data and 'session_id' in session_data:
        delete_session(session_data['session_id'])

    return None
```

**Integration Notes**:
- After session is cleared, `display_page()` will automatically redirect to login

---

## Data Flow

### Navigation Flow

```
User Journey 1: Home → Detail → Back to Home
================================================
1. User on home page (/)
   └─> Sees restaurant cards with random 4-5 star restaurants

2. User clicks restaurant card "Kyoto Sushi House"
   └─> Card Click Handler triggers
   └─> URL updates to /restaurant/42
   └─> selected-restaurant-id updates to {'id': 42}
   └─> previous-page-location updates to {'from': 'home'}

3. URL change triggers display_page()
   └─> Detects /restaurant/42 route
   └─> Calls create_restaurant_detail_page(42)

4. Detail page loads
   └─> Data Loader callback fetches restaurant ID 42 from database
   └─> restaurant-detail-data updates with full restaurant info
   └─> Content Renderer builds detail page layout

5. User clicks back button
   └─> Back Button Handler reads previous-page-location
   └─> URL updates to /
   └─> view-mode updates to 'home'
   └─> display_page() routes back to home


User Journey 2: List → Detail → Back to List
================================================
1. User on restaurant list page (/restaurant-list or view-mode='restaurant-list')
   └─> Sees paginated grid of restaurants

2. User clicks restaurant card in grid
   └─> Card Click Handler triggers
   └─> URL updates to /restaurant/127
   └─> selected-restaurant-id updates to {'id': 127}
   └─> previous-page-location updates to {'from': 'restaurant-list'}

3. Detail page loads (same as Journey 1, step 3-4)

4. User clicks back button
   └─> Back Button Handler reads previous-page-location
   └─> URL updates to /restaurant-list
   └─> view-mode updates to 'restaurant-list'
   └─> display_page() routes back to restaurant list


User Journey 3: Direct URL Access
================================================
1. User navigates directly to /restaurant/99 (e.g., from bookmark)
   └─> display_page() callback triggered with pathname='/restaurant/99'
   └─> Route Detector extracts restaurant ID 99
   └─> Page Router creates detail page

2. Detail page loads (same as Journey 1, step 4)

3. User clicks back button
   └─> No previous page context available
   └─> Defaults to home page (/)
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Action                               │
│                (Click Restaurant Card)                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Pattern-Matching Callback                      │
│            {'type': 'restaurant-card', 'index': 42}              │
│                       n_clicks = 1                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Update URL Pathname                             │
│                  url.pathname = '/restaurant/42'                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Route Detector Callback                        │
│    Input: pathname='/restaurant/42'                             │
│    Output: selected-restaurant-id={'id': 42}                    │
│            previous-page-location={'from': 'home'}               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ├──────────────────┐
                            ▼                  ▼
┌─────────────────────────────────┐  ┌──────────────────────────┐
│     Page Router Callback        │  │  Data Loader Callback    │
│ (display_page - MODIFIED)       │  │                          │
│                                  │  │  Fetch restaurant by ID  │
│ Routes to detail page layout    │  │  from database           │
│                                  │  │                          │
│ create_restaurant_detail_page()  │  │  get_restaurant_by_id()  │
└─────────────────┬───────────────┘  └──────────┬───────────────┘
                  │                              │
                  │                              ▼
                  │                   ┌──────────────────────────┐
                  │                   │  restaurant-detail-data  │
                  │                   │  (full restaurant dict)  │
                  │                   └──────────┬───────────────┘
                  │                              │
                  │                              ▼
                  │                   ┌──────────────────────────┐
                  │                   │ Content Renderer Callback│
                  │                   │                          │
                  │                   │ Build detail page layout │
                  │                   │ with restaurant data     │
                  │                   └──────────┬───────────────┘
                  │                              │
                  └──────────────────────────────┘
                                    ▼
                  ┌─────────────────────────────────────┐
                  │     Display Detail Page             │
                  │                                     │
                  │ - Header with back button           │
                  │ - Hero with restaurant image        │
                  │ - Two-column content layout         │
                  │ - All restaurant information        │
                  └─────────────────────────────────────┘
```

### State Synchronization

**dcc.Store Components Interaction**:

1. **session-store**: Persists across all page views
   - Checked by `display_page()` on every route change
   - If invalid, redirects to login regardless of requested route

2. **selected-restaurant-id**: Memory storage
   - Updated by Route Detector when URL changes
   - Triggers Data Loader to fetch restaurant info
   - Cleared when user navigates away from detail page

3. **restaurant-detail-data**: Memory storage
   - Populated by Data Loader
   - Consumed by Content Renderer
   - Cleared when user navigates away

4. **previous-page-location**: Memory storage
   - Set when navigating TO detail page
   - Read when navigating AWAY from detail page
   - Enables smart back button behavior

5. **view-mode**: Memory storage
   - Updated when navigating between home/list/detail
   - Used by `display_page()` for routing logic

**Callback Execution Order**:

```
URL Change → Route Detector → [Page Router + Data Loader (parallel)]
                                     ↓              ↓
                              Page Scaffold    Restaurant Data
                                     ↓              ↓
                                     └──────┬───────┘
                                            ↓
                                   Content Renderer
                                            ↓
                                   Complete Page Display
```

## Integration Notes

### Existing Code Reuse

**From `utils/database.py`**:
- `get_restaurant_by_id(restaurant_id)` - Already implemented, no changes needed
- Returns dict or None, perfect for our use case

**From `app.py`**:
- Authentication system - Works seamlessly with new routes
- User dropdown components - Reuse pattern for detail page
- Dark theme styling - Extend existing CSS classes
- Loading/error patterns - Apply to detail page states

**From `assets/voyage_styles.css`**:
- Card styling classes - Reference for detail page cards
- Color variables - Use #deb522 gold accent consistently
- Responsive breakpoints - Apply same breakpoints to detail page
- Button styles - Reuse btn-primary and btn-secondary

### Migration Steps

**Phase 1: Layout Foundation** (No callbacks yet)
1. Create layout helper functions in `app.py`:
   - `create_restaurant_detail_page(restaurant_id)`
   - `create_detail_header()`
   - `create_detail_hero(data)`
   - `create_location_section(data)`
   - `create_pricing_section(data)`
   - `create_categories_section(data)`
   - `create_map_placeholder_section(data)`
   - `create_ratings_breakdown_section(data)`
   - `create_statistics_section(data)`
   - `create_reviews_placeholder_section(data)`
   - `create_loading_state()`
   - `create_error_state(error_message)`

2. Add new CSS classes to `voyage_styles.css`:
   - Detail page structure classes
   - Information section cards
   - Rating display components
   - Loading and error states

3. Test layout rendering manually (without navigation)

**Phase 2: Data Storage Setup**
1. Add new `dcc.Store` components to app layout (line ~412):
   - `dcc.Store(id='selected-restaurant-id', storage_type='memory')`
   - `dcc.Store(id='restaurant-detail-data', storage_type='memory')`
   - `dcc.Store(id='previous-page-location', storage_type='memory')`

2. Test that stores initialize properly

**Phase 3: Navigation Infrastructure**
1. Modify `create_destination_card()` function (line ~173):
   - Wrap card in clickable `html.Div` with pattern-matching ID
   - Add `n_clicks=0` property

2. Modify restaurant list grid cards (line ~1688):
   - Add pattern-matching ID wrapper
   - Add `n_clicks=0` property

3. Add Route Detector callback (new)

4. Add Restaurant Card Click Handler callback (new)

5. Test card clicking and URL updates (should see URL change but page won't load yet)

**Phase 4: Page Routing**
1. Modify existing `display_page()` callback (line ~748):
   - Add `Input('selected-restaurant-id', 'data')` to inputs
   - Add route detection for `/restaurant/{id}`
   - Call `create_restaurant_detail_page()` when matched

2. Test navigation flow (should see detail page layout but no data yet)

**Phase 5: Data Loading**
1. Add Data Loader callback (new)
   - Fetches restaurant from database
   - Populates `restaurant-detail-data` store

2. Add Content Renderer callback (new)
   - Builds detail page with actual data
   - Handles loading and error states

3. Test complete flow: click card → see loading → see populated detail page

**Phase 6: Back Navigation**
1. Add Back Button Handler callback (new)

2. Test back navigation from detail page

**Phase 7: Detail Page Interactions**
1. Add User Dropdown Toggle callback for detail page

2. Add Logout callback for detail page

3. Test all detail page interactions

**Phase 8: Edge Cases and Polish**
1. Test direct URL access (`/restaurant/123`)
2. Test invalid restaurant ID
3. Test missing restaurant
4. Test logout from detail page
5. Test session expiration while on detail page
6. Add loading animations
7. Optimize database queries
8. Test responsive layout on mobile

### Breaking Changes

**None** - This feature is additive and does not modify existing functionality. All existing pages and callbacks continue to work as before.

**New Dependencies**:
- No new Python packages required
- All functionality uses existing Dash components and patterns

## Testing Strategy

### Unit Tests

**Test Data Access Functions**:
```python
def test_get_restaurant_by_id_valid():
    """Test fetching existing restaurant"""
    result = get_restaurant_by_id(1)
    assert result is not None
    assert result['Restaurant_ID'] == 1
    assert 'Name' in result

def test_get_restaurant_by_id_invalid():
    """Test fetching non-existent restaurant"""
    result = get_restaurant_by_id(999999)
    assert result is None

def test_get_restaurant_by_id_invalid_type():
    """Test with invalid ID type"""
    result = get_restaurant_by_id("invalid")
    assert result is None
```

**Test Layout Helper Functions**:
```python
def test_create_detail_hero():
    """Test hero section generation"""
    mock_data = {
        'Name': 'Test Restaurant',
        'JapaneseName': 'テスト',
        'TotalRating': 4.5
    }
    hero = create_detail_hero(mock_data)
    assert hero is not None
    # Check for expected components

def test_create_loading_state():
    """Test loading state rendering"""
    loading = create_loading_state()
    assert 'loading-container' in str(loading)

def test_create_error_state():
    """Test error state rendering"""
    error = create_error_state("Not found")
    assert 'Restaurant Not Found' in str(error)
```

### Integration Tests

**Test Callback Flow**:
```python
def test_route_detector_callback():
    """Test URL parsing to restaurant ID"""
    pathname = '/restaurant/42'
    result = detect_restaurant_route(pathname)
    assert result[0] == {'id': 42}
    assert result[1] == {'from': 'restaurant-list'}

def test_card_click_navigation():
    """Test clicking card updates URL"""
    # Simulate card click with restaurant_id=10
    # Verify URL updates to /restaurant/10

def test_back_button_from_home():
    """Test back navigation from detail (came from home)"""
    # Set previous_page_location to {'from': 'home'}
    # Click back button
    # Verify URL updates to /

def test_back_button_from_list():
    """Test back navigation from detail (came from list)"""
    # Set previous_page_location to {'from': 'restaurant-list'}
    # Click back button
    # Verify URL updates to /restaurant-list
```

### User Scenarios

**Scenario 1: Browse and View Restaurant from Home**
- [ ] User loads home page
- [ ] User sees restaurant cards
- [ ] User clicks on first restaurant card
- [ ] Detail page loads with correct information
- [ ] All sections display proper data (no NULL errors)
- [ ] Ratings display correctly with stars
- [ ] Prices display correctly or show "Not Available"
- [ ] User clicks back button
- [ ] User returns to home page (same position if possible)

**Scenario 2: Search, View, and Return**
- [ ] User navigates to restaurant list
- [ ] User searches for specific cuisine
- [ ] User clicks on search result
- [ ] Detail page loads
- [ ] User clicks back button
- [ ] User returns to restaurant list with search preserved

**Scenario 3: Direct URL Access**
- [ ] User opens browser and types `/restaurant/50`
- [ ] User is prompted to login (if not logged in)
- [ ] After login, detail page loads automatically
- [ ] All data displays correctly
- [ ] Back button goes to home page (default)

**Scenario 4: Invalid Restaurant ID**
- [ ] User navigates to `/restaurant/999999`
- [ ] Error page displays with friendly message
- [ ] Back button on error page works
- [ ] User is not stuck on error page

**Scenario 5: Session Expiration on Detail Page**
- [ ] User is viewing detail page
- [ ] Session expires (or simulate by clearing session-store)
- [ ] User clicks any link (back button, logout, etc.)
- [ ] User is redirected to login page
- [ ] After login, user is returned to home (not stuck)

**Scenario 6: Mobile Responsiveness**
- [ ] User views detail page on mobile device
- [ ] Two-column layout stacks to single column
- [ ] All sections are readable
- [ ] Back button is easily accessible
- [ ] Images scale properly
- [ ] No horizontal scrolling

## Implementation Checklist

### Step 1: Prepare Layout Functions
- [ ] Create `create_restaurant_detail_page()` skeleton function
- [ ] Create `create_detail_header()` with back button and user dropdown
- [ ] Create `create_detail_hero(data)` with image and main info
- [ ] Create `create_location_section(data)` with station and coordinates
- [ ] Create `create_pricing_section(data)` with dinner/lunch prices
- [ ] Create `create_categories_section(data)` with category tags
- [ ] Create `create_map_placeholder_section(data)` for future map
- [ ] Create `create_ratings_breakdown_section(data)` with detailed ratings
- [ ] Create `create_statistics_section(data)` with review count and category
- [ ] Create `create_reviews_placeholder_section(data)` for future reviews
- [ ] Create `create_loading_state()` with spinner
- [ ] Create `create_error_state(error_message)` with error display

### Step 2: Add CSS Styling
- [ ] Add `.detail-header-section` styles
- [ ] Add `.detail-hero-section` styles
- [ ] Add `.detail-main-content` and column styles
- [ ] Add `.info-section` card styles
- [ ] Add `.section-title` styles
- [ ] Add `.rating-display-large` styles
- [ ] Add `.rating-item` and `.stat-item` styles
- [ ] Add `.category-tag` styles
- [ ] Add `.price-item` styles
- [ ] Add `.loading-container` and `.error-container` styles
- [ ] Add responsive breakpoints for detail page
- [ ] Test CSS in isolation with mock data

### Step 3: Add State Storage
- [ ] Add `dcc.Store(id='selected-restaurant-id')` to app layout
- [ ] Add `dcc.Store(id='restaurant-detail-data')` to app layout
- [ ] Add `dcc.Store(id='previous-page-location')` to app layout
- [ ] Verify stores initialize properly

### Step 4: Modify Card Components
- [ ] Update `create_destination_card()` to add pattern-matching ID wrapper
- [ ] Update restaurant list grid card creation to add pattern-matching ID
- [ ] Test that cards still render correctly with new IDs

### Step 5: Add Route Detection
- [ ] Create `detect_restaurant_route()` callback
- [ ] Test URL parsing with various inputs
- [ ] Test with valid restaurant ID
- [ ] Test with invalid restaurant ID
- [ ] Test with non-restaurant routes

### Step 6: Modify Page Router
- [ ] Modify `display_page()` callback to accept `selected-restaurant-id` input
- [ ] Add route detection for `/restaurant/{id}` pattern
- [ ] Add call to `create_restaurant_detail_page()` when route matches
- [ ] Test routing to detail page (skeleton)
- [ ] Test that existing routes still work

### Step 7: Add Data Loading
- [ ] Create `load_restaurant_detail()` callback
- [ ] Test database query with valid ID
- [ ] Test with invalid ID
- [ ] Test error handling
- [ ] Verify data structure matches expectations

### Step 8: Add Content Rendering
- [ ] Create `render_restaurant_detail()` callback
- [ ] Test with complete restaurant data
- [ ] Test with missing fields (NULL handling)
- [ ] Test loading state display
- [ ] Test error state display

### Step 9: Add Card Click Handler
- [ ] Create `handle_card_click()` callback with pattern matching
- [ ] Test clicking cards on home page
- [ ] Test clicking cards on restaurant list page
- [ ] Verify URL updates correctly

### Step 10: Add Back Navigation
- [ ] Create `handle_back_button()` callback
- [ ] Test back navigation from home origin
- [ ] Test back navigation from list origin
- [ ] Test default behavior (no origin data)

### Step 11: Add Detail Page Interactions
- [ ] Create `toggle_user_dropdown_detail()` callback
- [ ] Create `logout_from_detail_page()` callback
- [ ] Test dropdown toggle
- [ ] Test logout functionality
- [ ] Verify redirection after logout

### Step 12: Edge Case Testing
- [ ] Test direct URL access to `/restaurant/123`
- [ ] Test invalid restaurant ID in URL
- [ ] Test non-existent restaurant
- [ ] Test with missing database connection
- [ ] Test session expiration on detail page
- [ ] Test rapid navigation (clicking multiple cards quickly)

### Step 13: Responsive Testing
- [ ] Test on desktop (1920px width)
- [ ] Test on tablet (768px width)
- [ ] Test on mobile (375px width)
- [ ] Verify two-column layout stacks properly
- [ ] Verify images scale correctly
- [ ] Verify text is readable on all screen sizes

### Step 14: Performance Testing
- [ ] Measure page load time for detail page
- [ ] Verify database query time is acceptable (< 100ms)
- [ ] Check for memory leaks with repeated navigation
- [ ] Verify no unnecessary re-renders

### Step 15: Documentation
- [ ] Update CLAUDE.md with detail page architecture
- [ ] Document new callbacks
- [ ] Document new layout functions
- [ ] Document URL routing patterns
- [ ] Add code comments for complex logic

## Additional Considerations

### Performance Optimization

**Database Query Optimization**:
- Restaurant ID is primary key → already indexed
- Single query per detail page load
- Typical query time: < 10ms
- No N+1 query problems

**Rendering Optimization**:
- Use `prevent_initial_call=True` for data loading callbacks
- Separate data fetching from rendering (two callbacks)
- Avoid nested callbacks where possible
- Use pattern matching for scalable card clicking

**Caching Strategy** (Future Enhancement):
- Consider caching frequently accessed restaurants
- Use `dcc.Store` with longer expiry for popular restaurants
- Implement server-side caching for database queries

### Accessibility

**Keyboard Navigation**:
- Ensure back button is keyboard accessible (native HTML button)
- Restaurant cards should be focusable (use `tabIndex=0` on wrapper divs)
- Dropdown menu should work with keyboard (existing implementation already handles this)

**Screen Readers**:
- Add ARIA labels to sections: `aria-label="Location Information"`
- Add alt text to images (currently using placeholder)
- Ensure rating displays have text alternatives

**Visual Accessibility**:
- Maintain 4.5:1 contrast ratio for text (white on dark background: ✓)
- Use relative font sizes (rem/em) for scalability
- Ensure interactive elements have clear focus states

### Security Considerations

**Input Validation**:
- Restaurant ID from URL is parsed as integer
- Invalid IDs return None, not database errors
- No SQL injection risk (using parameterized queries)

**Authentication**:
- All detail page routes check session validity
- Expired sessions redirect to login
- No sensitive data exposed in error messages

**Data Exposure**:
- Only public restaurant information displayed
- No user data or admin-only fields exposed
- Reviews (future) should be public-facing data only

### Future Enhancements

**Phase 2 Features** (Not in current blueprint):

1. **Interactive Map Integration**:
   - Replace map placeholder with actual map component
   - Use Lat/Long coordinates from database
   - Show restaurant location pin
   - Add nearby restaurants markers

2. **Reviews Display**:
   - Query reviews table (if exists)
   - Display user reviews with ratings and dates
   - Add pagination for large review sets
   - Add review sorting (newest, highest rated, etc.)

3. **Image Gallery**:
   - Add multiple images per restaurant (requires new data source)
   - Implement image carousel/lightbox
   - Support user-uploaded images (requires upload feature)

4. **Favorite/Bookmark Feature**:
   - Add heart icon to save restaurant to favorites
   - Store in user's favorites list (new database table)
   - Show saved status on detail page

5. **Share Functionality**:
   - Add share button for social media
   - Generate shareable link with restaurant ID
   - Create Open Graph meta tags for link previews

6. **Similar Restaurants**:
   - Query database for restaurants with similar categories
   - Display as "You might also like" section at bottom
   - Use TF-IDF or category matching algorithm

7. **Reservation Integration**:
   - Add "Reserve Table" button
   - Integrate with external booking system
   - Display availability calendar

8. **Print-Friendly View**:
   - Add print stylesheet
   - Optimize layout for printing
   - Include QR code for restaurant URL

### Maintenance Notes

**Regular Checks**:
- Verify database connection on app startup
- Check for broken restaurant IDs (if data is updated)
- Monitor callback performance metrics
- Review error logs for failed detail page loads

**Database Updates**:
- When restaurant data is updated, no code changes needed
- Adding new fields: update layout functions to display them
- Removing fields: add NULL checks in layout functions

**Scaling Considerations**:
- Current design handles 1,000s of restaurants efficiently
- If database grows to 100,000+ restaurants, consider:
  - Adding database connection pooling
  - Implementing Redis cache for hot restaurants
  - Using lazy loading for image galleries

---

## Summary

This blueprint provides a complete architectural plan for implementing a restaurant detail page feature in the Voyage Dash application. The design follows these principles:

**Scalability**: Pattern-matching callbacks and database-driven design support unlimited restaurants

**Maintainability**: Clear separation of concerns between routing, data loading, and rendering

**User Experience**: Smooth navigation, loading states, error handling, and consistent dark theme

**Integration**: Minimal changes to existing code, reuses authentication and styling systems

**Future-Proof**: Designed with placeholders for maps, reviews, and other enhancements

The implementation can proceed step-by-step following the checklist, with each phase independently testable. The architecture supports direct URL access, back navigation, and maintains session state throughout the user journey.
