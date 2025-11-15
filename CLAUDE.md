# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Dash web application called "Voyage" - a modern travel discovery platform for Kyoto featuring both restaurants and hotels with integrated user authentication. The application provides:

**Restaurant Features**:
- Advanced search with multi-criteria filtering (keyword, cuisine, rating, price, station, review count)
- Paginated restaurant grid (12 per page) with sortable results
- Individual restaurant detail pages with ratings, reviews, pricing, location, and interactive review filtering
- Real-time search suggestions and filter chips
- Search history (session-based) and popular searches (persistent)

**Hotel Features** (Recently Added):
- Hotel search with type filtering and keyword search
- Paginated hotel grid display
- Individual hotel detail pages with ratings, location, and nearby hotel recommendations
- Hotel type categorization and filtering

**Core Features**:
- Session-based authentication with login/registration (SQLite)
- Dark theme UI with gold accent color (#deb522)
- SQLite database architecture for efficient data querying
- URL-based routing for detail pages
- Responsive card-based layouts

## Development Commands

### Setup
```bash
# Create virtual environment (venv or conda)
pip install -r requirements.txt
```

### Run Application
```bash
python app.py
```
The app runs on default Dash port (usually http://127.0.0.1:8050) with `debug=True`.

### Database Setup
```bash
# First-time setup: Migrate CSV data to SQLite
python migrate_to_db.py               # Creates ./data/restaurants.db

# Test database functionality
python performance_test.py            # Compare CSV vs database performance
```

**Important**: The application requires SQLite database to run. If `restaurants.db` doesn't exist, run `migrate_to_db.py` first.

### Data Generation and Testing
```bash
# Data generation utilities
python generate_reviews.py                        # Generate synthetic review data
python change_totalRating.py                      # Update restaurant ratings from reviews
python Hotel_Generate.py                          # Generate hotel data
python Hotel_Separate.py                          # Separate hotel data into CSV files

# Testing scripts (standalone Dash apps)
python test_restaurant_barChart.py                # Test rating visualizations
python test_rating_distribution.py                # Test rating distribution analysis
python test_reviews_join.py                       # Test review data joins
```

## Architecture

### Main Application (app.py)

**Large monolithic file** (3700+ lines) organized into sections:

1. **Imports & Setup** (lines 1-45): Dash, Plotly, Pandas imports; utility imports from `utils/`, `pages/`
2. **Data Loading** (lines 46-150): Database connection, helper functions for options creation
3. **Restaurant UI Components** (lines 151-1000): Search bars, cards, list layouts, detail layouts
4. **Hotel UI Components** (lines 1001-1700): Hotel cards, search bars, list layouts, detail layouts
5. **Main Layouts** (lines 1701-1900): Homepage layout with stores and navigation
6. **App Initialization** (lines 1901-1950): Dash app setup, external stylesheets, layout definition
7. **Callbacks - Authentication** (lines 1951-2100): Login, register, logout, page routing
8. **Callbacks - Navigation** (lines 2101-2200): Page navigation, back buttons
9. **Callbacks - Restaurant Features** (lines 2201-2800): Search, filters, pagination, detail pages
10. **Callbacks - Hotel Features** (lines 2801-3200): Hotel search, filtering, detail pages
11. **Callbacks - UI Components** (lines 3201-3700): Dropdowns, tabs, user menus
12. **App Runner** (line 3700+): `if __name__ == '__main__': app.run(debug=True)`

### Database Module (utils/database.py)

**Restaurant Functions**:
- `get_all_restaurants()`: Fetch all restaurants with optional sorting
- `get_random_top_restaurants(n, min_rating)`: Get random high-rated restaurants
- `search_restaurants(keyword, cuisine, rating, price_range, stations, min_reviews, sort_by)`: Advanced search with SQL WHERE clauses
- `get_unique_stations()`: List all unique station names
- `get_unique_cuisines()`: List all unique cuisine types
- `get_restaurant_by_id(id)`: Fetch single restaurant details
- `get_nearby_restaurants(lat, lon, limit, exclude_id)`: Find nearby restaurants by coordinates

**Hotel Functions**:
- `get_all_hotels()`: Fetch all hotels
- `get_hotel_by_id(id)`: Fetch single hotel details
- `get_random_top_hotels(n, min_rating)`: Get random high-rated hotels
- `search_hotels(keyword, hotel_type, min_rating, sort_by)`: Search hotels with filters
- `get_unique_hotel_types()`: List all unique hotel types
- `get_nearby_hotels(lat, lon, limit, exclude_id)`: Find nearby hotels by coordinates
- `get_hotels_by_type(type_name)`: Filter hotels by type

**Connection Management**:
```python
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables column name access
    try:
        yield conn
    finally:
        conn.close()
```

All queries use this context manager for automatic connection cleanup.

### Authentication Module (utils/auth.py)

- `init_db()`: Initialize SQLite database with users and sessions tables
- `create_user(username, password, email)`: Create new user with SHA-256 hashed password
- `verify_user(username, password)`: Validate credentials and update last login
- `create_session(user_id, remember_me)`: Create session (2 hours or 30 days)
- `get_session(session_id)`: Validate and retrieve session
- `delete_session(session_id)`: Remove session (logout)
- `clean_expired_sessions()`: Remove expired sessions

**Test Accounts**: Auto-created on first run
- `admin` / `admin123`
- `demo` / `demo123`

Database: `./data/users.db`

### Pages Package (pages/)

**login_page.py**:
- `create_login_layout()`: Login page with username/password form
- `create_register_layout()`: Registration page with validation

### Data Files (data/)

**Active Databases**:
- `restaurants.db`: SQLite database for restaurant data
  - Table: `restaurants` - All restaurant information with indexes
  - Indexes: `idx_name`, `idx_station`, `idx_first_category`, `idx_total_rating`, `idx_rating_category`, `idx_review_num`
- `users.db`: SQLite database for authentication (auto-created)
  - Tables: `users`, `sessions`

**CSV Source Files** (used for migration):
- `Kyoto_Restaurant_Info_Full.csv`: Restaurant source data
- `Reviews.csv`: Review source data
- `Hotels.csv`: Hotel data
- `HotelTypes.csv`: Hotel type mappings
- `Kyoto_Hotels_Full.csv`: Complete hotel dataset
- `Types.csv`: Type categorization

**Legacy CSV Files** (referenced in code but may not exist):
- `Restaurant.csv`, `Category.csv`, `Price.csv`, `Rating.csv`, `RestaurantCategory.csv` - Normalized table structure (legacy)

### Assets (assets/)

**Stylesheets**:
- `voyage_styles.css`: Main application styles for modern homepage, cards, detail pages
- `enhanced_search_styles.css`: Advanced search components, filters, chips, suggestions
- `login_styles.css`: Authentication page styles (legacy)
- `gear_menu.css`: Hamburger menu styles (legacy, unused)

**Images**:
- `logo.png`: Application logo
- `Hazuki.jpg`: Hero background and card placeholder
- `Roger.jpg`: Alternative card image
- `food_dirtyrice.png`: Food imagery

**Icons**: `earth.svg`, `user.svg`, `calendar.svg` (legacy)
**JavaScript**: `dropdown_handler.js`: Client-side dropdown interactivity

## URL Routing and Navigation

The app uses URL-based routing with three main page types:

1. **Homepage** (`/`):
   - Hero section with search bar
   - Random selection of 10 top-rated restaurants (4-5 stars)
   - Tab navigation (Saved Trips / Wishlisted Hotels / Favorite Restaurants)
   - Inspiration grid

2. **Restaurant List Page** (`/restaurants` - view-mode state):
   - Paginated grid (12 per page)
   - Advanced search and filtering
   - Database queries via `search_restaurants()`

3. **Restaurant Detail Page** (`/restaurant/<restaurant_id>`):
   - URL parsing extracts restaurant ID
   - Fetches data via `get_restaurant_by_id()`
   - Interactive review filtering by rating
   - Back button with state preservation

4. **Hotel List Page** (`/hotels` - view-mode state):
   - Paginated hotel grid
   - Hotel type filtering and keyword search
   - Database queries via `search_hotels()`

5. **Hotel Detail Page** (`/hotel/<hotel_id>`):
   - URL parsing extracts hotel ID
   - Fetches data via `get_hotel_by_id()`
   - Displays nearby hotels using `get_nearby_hotels()`
   - Back button navigation

**Routing Implementation**:
- `dcc.Location` component tracks URL
- Pattern matching callbacks handle dynamic card clicks
- State stores track previous page for proper back navigation
- URL changes trigger page re-renders via callback chain

## Key Data Flow

### Authentication Flow
1. App loads → check `session-store` → validate session → route to login or main app
2. Login: verify credentials → create session (UUID) → store in database and session storage
3. Logout: delete session from database → clear session storage → redirect to login
4. Register: validate inputs → hash password (SHA-256) → store in database

### Database Architecture (Important!)
**On first run**: Execute `migrate_to_db.py` to create `restaurants.db` from CSV files
**App startup**: Import `utils/database.py` (no CSV loading, only connection string)
**On-demand queries**: All data fetched via SQL with proper indexing

**Benefits**:
- Faster startup (no CSV parsing on every launch)
- Efficient filtering (SQL WHERE clauses with indexes)
- Lower memory usage (query only what's needed)
- Better scalability
- Concurrent access support

### Search & Filter Flow
1. User types keyword → debounce 300ms → generate suggestions → display dropdown
2. User selects filter → update active filter chips → trigger search
3. Search executes → SQL query with all active filters → update results store
4. Results store change → update grid display and pagination
5. Search saved to history (session storage) and popular searches (local storage)

## Callback Architecture

The app uses 40+ callbacks organized by functionality:

**Authentication Callbacks** (6):
- Page routing based on session state
- Login/register form handlers
- Logout from different pages (home, restaurant list, detail, hotel list)

**Navigation Callbacks** (5):
- Navigate to restaurant list
- Navigate to hotel list
- Back button handlers (using pattern matching)
- View mode updates

**Restaurant Callbacks** (15+):
- Search suggestions display
- Advanced filters toggle
- Cuisine/rating dropdown toggles (mutual exclusivity)
- Active filter chips display
- Search handlers (preview and full search)
- Restaurant grid updates with pagination
- Restaurant detail page loading
- Review filtering by rating

**Hotel Callbacks** (10+):
- Hotel search handlers
- Hotel type filtering
- Hotel grid updates with pagination
- Hotel detail page loading
- Nearby hotels display
- Hotel card click navigation

**UI Component Callbacks** (10+):
- User dropdown toggles (separate for each page)
- Tab navigation (Saved/Wishlisted/Favorites)
- Inspiration grid population
- Destination cards population

**Technical Details**:
- **Pattern Matching**: Used for dynamic elements (`{'type': 'card', 'index': ALL}`)
- **State Management**: Multiple `dcc.Store` components with different storage types:
  - `'session'`: Auth session, search history, page mode
  - `'memory'`: View mode, dropdown state, search results, pagination
  - `'local'`: Popular searches (persistent across sessions)
- **Prevent Update**: Most callbacks use `prevent_initial_call=True` or `PreventUpdate`
- **Allow Duplicate**: Many outputs use `allow_duplicate=True` for multiple callbacks updating same component

## Important Implementation Patterns

### Pattern Matching Callbacks
The app extensively uses Dash's pattern matching for dynamic elements:
```python
Input({'type': 'restaurant-card', 'index': ALL}, 'n_clicks')
Input({'type': 'hotel-card', 'index': ALL}, 'n_clicks')
Input({'type': 'page-btn', 'index': ALL}, 'n_clicks')
```
This handles clicks on dynamically generated cards without hardcoding each callback.

### State Store Strategy
- `session-store`: User authentication session ID
- `page-mode`: Controls login/register/main app routing
- `view-mode`: Controls home/restaurant-list/hotel-list page display
- `dropdown-open`: Tracks user dropdown menu state (separate for each page)
- `search-results-store`: Current search results as list of dicts
- `current-page-store`: Pagination current page number
- `selected-restaurant-id` / `selected-hotel-id`: IDs for detail pages
- `restaurant-detail-data` / `hotel-detail-data`: Cached data for detail pages

### Database Query Pattern
All queries use context manager:
```python
with get_db_connection() as conn:
    query = "SELECT * FROM restaurants WHERE ..."
    df = pd.read_sql_query(query, conn, params=params)
```

### Search Debouncing
Search input uses `debounce=300` (300ms) to avoid excessive queries while typing.

## Legacy Code (Unused)

The codebase contains legacy code from a previous travel analysis dashboard that is no longer used:

**Legacy Features** (code exists but not in current UI):
- Multi-tab dashboard (Overview/Trip Planner/Attractions)
- Travel dataset analysis with visualizations (bar/pie/map/box charts)
- Country comparison with scoring algorithm
- Geocoding for attractions mapping
- Hamburger menu navigation

**Legacy Utils** (in `utils/` but unused):
- `const.py`: Dashboard constants and metrics
- `data_clean.py`: Travel data cleaning pipeline
- `data_transform.py`: Trip scoring and filtering
- `data_validation.py`: Validation utilities
- `visualization.py`: Plotly chart generation (partially used)

**When Modifying Code**: Check if you're working with current features (restaurant/hotel discovery) or legacy features (travel analysis). Many utility functions are no longer called by current `app.py`.

## Troubleshooting

### Database Issues
- **"No such table: restaurants"**: Run `python migrate_to_db.py` to create database
- **Database locked errors**: Only one process can write to SQLite at a time
- **Slow search performance**: Check that indexes were created during migration
- **Missing data**: Verify CSV source files exist before migration

### Authentication Issues
- **Session not persisting**: Verify `session-store` uses `storage_type='session'`
- **Can't login**: Check `./data/users.db` exists; delete and restart to recreate
- **Session expires quickly**: Default is 2 hours; check "Remember me" for 30 days

### UI Issues
- **Cards not showing**: Check browser console; verify database has data
- **Images not displaying**: Ensure `assets/Hazuki.jpg` and `assets/logo.png` exist
- **Search not working**: Check browser console for callback errors
- **Pagination broken**: Check `current-page-store` and `search-results-store` in DevTools
- **Detail page errors**: Verify restaurant/hotel ID in URL is valid

### Callback Issues
- **PreventUpdate errors**: Ensure all inputs exist in layout before callbacks fire
- **Circular callback errors**: Verify `allow_duplicate=True` is used when needed
- **Pattern matching not working**: Ensure dictionary IDs have exact same keys in layout and callback

### Performance Issues
- **Slow startup**: Normal for Dash; database mode should be faster than CSV
- **Slow search**: Check SQL query performance; consider adding more indexes
- **Too many callbacks firing**: Use `prevent_initial_call=True` to avoid unnecessary updates

## Important Notes

**Current State**:
- App implements modern restaurant and hotel discovery platform (Voyage)
- SQLite database with 2000+ Kyoto restaurants and hotels
- Active development on search, filtering, pagination, and detail pages
- Personalized features (saved/wishlisted) have UI but no backend yet

**Authentication & Security**:
- Login required on startup (test accounts: `admin`/`admin123`, `demo`/`demo123`)
- Session management with 2-hour expiry (30 days with "remember me")
- SHA-256 password hashing (consider bcrypt/argon2 for production)
- `users.db` auto-created on first run

**Technical Details**:
- Dark theme with gold accent (`#deb522`)
- FontAwesome 6.4.0 icons, Bootstrap theme
- 12 items per page for both restaurants and hotels
- `Hazuki.jpg` used as hero background and card placeholder
