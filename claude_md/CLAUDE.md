# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Dash web application called "Voyage" - a modern restaurant discovery platform for Kyoto restaurants with integrated user authentication. The application features:
- **Modern Homepage**: Hero section with background image, advanced search interface, and curated restaurant recommendations
- **Restaurant Discovery**: Browse and search 2000+ restaurants from Kyoto with ratings, categories, prices, and locations
- **Advanced Search**: Multi-criteria search with keyword input, cuisine filters, rating filters, price ranges, station selection, and review count minimums
- **Real-time Features**: Search suggestions, filter chips, search history (session-based), and popular searches (persistent)
- **Restaurant List Page**: Paginated grid view with 12 restaurants per page, advanced filtering, and sorting options
- **Restaurant Detail Pages**: Individual pages for each restaurant showing ratings, reviews, pricing, location, categories, and interactive review filtering by rating
- **Personalized Content**: Saved trips, wishlisted hotels, and favorite restaurants organized by tabs (UI implemented, backend pending)
- **Inspiration Section**: Travel articles and guides organized in a grid layout

The application includes a complete authentication system with login, registration, session management (SQLite-based), and page access protection. The UI uses a dark theme with gold accent color (#deb522) and modern card-based layouts.

**Data Architecture**: Uses SQLite database (`./data/restaurants.db`) for efficient querying instead of loading CSV files into memory. First-time setup requires running `migrate_to_db.py` to create the database from CSV sources.

**Note**: The codebase contains legacy travel analysis code (Overview, Trip Planner, Attractions) in `utils/` but the current `app.py` implements a restaurant-focused platform. The CSV files `Travel_dataset.csv`, `country_info.csv`, and `Attractions.csv` are referenced in code but may be missing from the data folder.

## Development Commands

### Setup
```bash
# Create virtual environment (venv or conda)
# Install dependencies
pip install -r requirements.txt
```

### Run Application
```bash
python app.py
```

The app runs on default Dash port (usually http://127.0.0.1:8050). App automatically runs with `debug=True` (see line 649 in app.py).

### Database Setup and Migration
```bash
# Migrate CSV data to SQLite database (one-time setup)
python migrate_to_db.py               # Creates ./data/restaurants.db from CSV files

# Test database functionality
python test_database.py               # Verify all database queries work correctly
python performance_test.py            # Compare CSV vs database performance
```

**Note**: The application now uses SQLite database instead of loading CSV files on every startup. This significantly improves loading speed and query performance.

### Testing and Utilities
```bash
# Run test scripts (standalone Dash apps for testing components)
python test_restaurant_barChart.py     # Restaurant rating visualization testing
python test_rating_distribution.py     # Rating distribution analysis
python test_reviews_join.py           # Review data join testing
python test_login_page.py             # Login page component testing

# Data generation and transformation utilities
python generate_reviews.py                        # Generate synthetic review data
python change_totalRating.py                      # Update restaurant total ratings from reviews
python restore_prices_and_add_price_category.py  # Process pricing data
```

## Current vs Legacy Architecture

**IMPORTANT**: This codebase is in transition. The `app.py` file has been completely redesigned, but legacy utility code remains.

### Current Implementation (app.py)
- **UI**: Three-page application (Homepage, Restaurant List, Restaurant Detail)
- **Data**: SQLite database (`restaurants.db`) with 2000+ Kyoto restaurants, migrated from CSV
- **Features**:
  - Advanced search with real-time suggestions and filter chips
  - Paginated restaurant grid (12 per page)
  - URL-based routing for restaurant detail pages (`/restaurant/<id>`)
  - Interactive review filtering by rating
  - Session-based authentication
  - Search history and popular searches tracking
- **Callbacks**: 30+ callbacks using pattern matching, state management, and database queries
- **Styles**: `voyage_styles.css` for layouts, `enhanced_search_styles.css` for search components
- **Components**: Modular search components in `components/` and callbacks in `callbacks/`

### Legacy Code (still in codebase but unused)
- **UI**: Multi-tab dashboard (Overview/Trip Planner/Attractions) with hamburger menu
- **Data**: Travel datasets, country info, attractions, safety metrics
- **Features**: Data visualizations (bar/pie/map/box), trip scoring, geocoding
- **Utils**: `data_transform.py`, `data_clean.py`, `visualization.py` functions
- **Style**: `gear_menu.css`, `login_styles.css`

**When modifying code**: Check if you're working with current features (restaurant homepage) or legacy features (travel analysis). Many functions in `utils/` are no longer called by `app.py`.

## Architecture

### Main Application (`app.py`)

**Structure** (3000+ lines organized into sections):

1. **Imports & Setup** (lines 1-62):
   - Dash, Plotly, Pandas, SQLite imports
   - Utility and component imports from `utils/`, `pages/`, `components/`, `callbacks/`
   - Database module imports for all query functions

2. **Data Loading** (lines 63-90):
   - Database connection via `utils/database.py`
   - Helper functions: `get_random_top_restaurants()`, `remove_parentheses()`, `create_cuisine_options()`

3. **UI Component Functions** (lines 91-700):
   - `create_compound_search_bar()`: Main search interface with dropdowns and filters
   - `create_destination_card()`: Restaurant card component with image, rating, category
   - `create_saved_trip_card()`: Saved trip card (UI only)
   - `create_add_new_card()`: Add new card placeholder
   - `create_inspiration_card()`: Inspiration article card
   - `create_restaurant_list_layout()`: Full restaurant list page with grid and pagination
   - `create_restaurant_detail_layout()`: Detail page layout with all restaurant info
   - Helper components: `create_header_section()`, `create_image_gallery()`, `create_reviews_section()`, etc.

4. **Main Layouts** (lines 701-900):
   - `create_main_layout()`: Homepage with hero, search, cards, tabs, inspiration
   - Layout includes all `dcc.Store` components for state management

5. **App Initialization** (lines 901-950):
   - Dash app creation with Bootstrap CSS
   - External stylesheets (FontAwesome, voyage_styles.css)
   - Suppress callback exceptions for dynamic layout
   - App layout with `dcc.Location` and page content container

6. **Callbacks - Authentication** (lines 951-1100):
   - Page routing (login/register/main)
   - Login handler with session creation
   - Register handler with validation
   - Page mode switches

7. **Callbacks - Navigation** (lines 1101-1200):
   - View mode changes (home/restaurant-list)
   - Back button handlers
   - Navigation triggers

8. **Callbacks - User Dropdown** (lines 1201-1350):
   - Three separate dropdown toggle callbacks (home, list, detail pages)
   - Three logout callbacks (one per page)

9. **Callbacks - Homepage UI** (lines 1351-1600):
   - Populate destination cards on load
   - Tab navigation between saved/wishlisted/favorites
   - Inspiration grid population

10. **Callbacks - Search & Filters** (lines 1601-2200):
    - Search suggestions display
    - Advanced filters toggle
    - Clear all filters
    - Cuisine and rating dropdown toggles (mutual exclusivity)
    - Option selection handlers
    - Active filter chips display
    - Search handlers (home preview and list page full search)

11. **Callbacks - Restaurant List Page** (lines 2201-2400):
    - Initialize with all restaurants
    - Update grid and pagination based on results
    - Handle pagination button clicks

12. **Callbacks - Restaurant Detail Page** (lines 2401-2600):
    - URL parsing and ID extraction
    - Data loading from database
    - Content rendering
    - Card click navigation
    - Back button handling
    - Review filtering by rating

13. **App Runner** (lines 2601+):
    - `if __name__ == '__main__': app.run(debug=True)`

**Key Functions**:
- UI rendering functions return `html.Div()` components
- Callbacks use `@app.callback()` decorator with inputs, outputs, and states
- Database queries integrated directly in callbacks via `utils/database.py` functions
- All styling uses inline styles or CSS classes from `voyage_styles.css`

### Utils Package (`utils/`)

**Note**: Most utilities are designed for legacy travel analysis features. Current app.py uses primarily `auth.py` and `database.py` for core functionality.

**`const.py`**: Constants and configuration
- `ALERT_RANK_MAP`: Travel alert severity mapping (灰色=2, 黃色=3, 橙色=4) - legacy
- `ALL_COMPARE_METRICS`: List of metrics for country comparison charts - legacy
- `TAB_STYLE`: UI styling for tab components (gold/black theme)
- `get_constants()`: Computes dashboard statistics (countries, travelers, nationalities, avg days) - legacy

**`data_clean.py`**: Data cleaning pipeline (legacy travel features)
- `travel_data_clean()`: Converts cost strings to float, parses dates, creates age groups and monthly bins
- `countryinfo_data_clean()`: Removes null values from country info
- `data_merge()`: Left joins travel data with country info on 'Destination'

**`data_transform.py`**: Business logic and filtering (legacy travel features)
- `preprocess_travel_df()`: Calculates daily/trip accommodation costs
- `filter_by_cost_and_types()`: Filters by accommodation cost range and types
- `pick_country_level()`: Aggregates trip-level data to country-level
- `filter_by_alert_and_visa()`: Applies travel alert threshold and visa-exempt filtering
- `compute_scores()`: Calculates weighted scores (0-100) combining safety and cost metrics
- `prepare_country_compare_data()`: Prepares data for comparison charts (max 5 countries)
- `get_dashboard_default_values()`: Returns default dropdown values for visualizations

**`data_validation.py`**: Helper utilities
- `is_exempt()`: Validates visa exemption status - legacy
- `minmax()`: MinMax normalization (0-1 range) with edge case handling
- `fmt()`: Number formatting for display

**`visualization.py`**: Plotly chart generation (mostly legacy)
- `build_compare_figure()`: Creates radar/bar/line charts with MinMax normalization
- `generate_bar()`, `generate_pie()`, `generate_map()`, `generate_box()`: Travel visualizations
- `build_table_component()`: Creates sortable/filterable Dash DataTable
- `generate_stats_card()`: Top-level statistics cards with icons
- All charts use dark theme (`plotly_dark`) with golden accent color (`#deb522`)

**`auth.py`**: Authentication and user management (actively used)
- `init_db()`: Initializes SQLite database with users and sessions tables
- `create_user()`: Creates new user with SHA-256 hashed password
- `verify_user()`: Validates username/password and updates last login time
- `create_session()`: Creates new session with expiration time
- `get_session()`: Retrieves and validates session by ID
- `delete_session()`: Removes session (logout)
- `clean_expired_sessions()`: Removes expired sessions from database
- Database location: `./data/users.db`
- Auto-creates test accounts: `admin`/`admin123` and `demo`/`demo123`

**`database.py`**: Restaurant data access layer (actively used)
- `get_all_restaurants()`: Fetch all restaurants with optional sorting
- `get_random_top_restaurants()`: Get random high-rated restaurants
- `search_restaurants()`: Advanced search with keyword, cuisine, rating, price, station filters
- `get_unique_stations()`: Get list of all unique station names
- `get_unique_cuisines()`: Get list of all unique cuisine types
- `get_restaurant_by_id()`: Fetch single restaurant by ID
- `get_top_rated_restaurants()`: Get highest rated restaurants with minimum review threshold
- `get_restaurants_by_category()`: Filter by rating category
- `get_restaurant_count()`: Get total number of restaurants
- Database location: `./data/restaurants.db`
- All queries use SQL with proper indexing for optimal performance

### Components Package (`components/`)

**`enhanced_search.py`**: Advanced search UI components (actively used)
- `create_enhanced_search_bar()`: Main search interface with keyword input, cuisine/rating dropdowns, filters toggle, and search button
- `create_search_stores()`: Creates dcc.Store components for search history, suggestions, active filters, and popular searches
- `create_suggestion_item()`: Generates individual search suggestion items with icons
- `create_filter_chip()`: Creates removable filter chips to show active filters
- `create_history_item()`: Renders search history entries with timestamps
- `create_popular_item()`: Displays popular search terms with search counts
- `generate_search_suggestions()`: Generates real-time suggestions based on keyword input (searches restaurants, cuisines, stations)
- `apply_advanced_filters()`: Applies price, station, review count, and sorting filters
- `add_to_search_history()`: Manages search history (max 10 entries)
- `update_popular_searches()`: Tracks and updates popular search statistics
- `get_top_popular_searches()`: Retrieves most frequently searched terms
- Helper functions: `get_price_category()` for price classification

### Callbacks Package (`callbacks/`)

**`search_callbacks.py`**: Search functionality callbacks (actively used)
- `register_search_callbacks()`: Registers all search-related callbacks to the app
- Real-time search suggestions based on user input
- Advanced filters toggle and collapse management
- Clear search and clear all filters functionality
- Cuisine and rating dropdown toggles with mutual exclusivity
- Active filter chips display and individual chip removal (using pattern matching)
- Comprehensive search handling with history and popular search tracking
- Search history display with relative timestamps
- Popular searches display with counts
- Click handlers for history/popular items to replay searches
- Live search trigger for auto-search on input change
- Search sidebar visibility toggle

**Key Callback Features**:
- Pattern Matching Callbacks (ALL) for dynamic filter chip removal
- Debounced search with 300ms delay on input
- Search history stored in session storage (persists until browser close)
- Popular searches stored in local storage (long-term persistence)
- Automatic filter state synchronization across UI components

### Pages Package (`pages/`)

**`login_page.py`**: UI components for authentication
- `create_login_layout()`: Login page with username/password form, "remember me" checkbox, and registration link
- `create_register_layout()`: Registration page with username, email, password, and password confirmation fields
- Both layouts use consistent dark theme with gold accent (`#deb522`)
- Requires `assets/login_styles.css` for custom styling

### Assets Package (`assets/`)

Contains static resources for the application:
- `voyage_styles.css`: Main application styles for modern homepage layout, restaurant cards, and detail pages
- `enhanced_search_styles.css`: Styles for advanced search components, filters, chips, and suggestions
- `login_styles.css`: Authentication page styles (legacy, may not be actively used)
- `gear_menu.css`: Hamburger menu navigation styles (legacy, may not be actively used)
- `logo.png`: Application logo displayed on login/register pages
- `Hazuki.jpg`: Hero background image and placeholder for cards
- `earth.svg`, `user.svg`, `calendar.svg`: UI icons (legacy)
- `bg_hamburger.png`: Background for menu button (legacy)

### Data Files (`data/`)

**Active Data Files:**
- `restaurants.db`: SQLite database for restaurant data (created by `migrate_to_db.py`)
  - Table: `restaurants` - All restaurant information with indexed columns for fast queries
  - Table: `reviews` - User reviews linked to restaurants
  - Indexes: `idx_name`, `idx_station`, `idx_first_category`, `idx_total_rating`, `idx_rating_category`, `idx_review_num`
- `users.db`: SQLite database for authentication (auto-created on first run)
  - Tables: `users` (id, username, password_hash, email, created_at, last_login)
  - Tables: `sessions` (session_id, user_id, created_at, expires_at)

**Source CSV Files (used for migration only):**
- `Kyoto_Restaurant_Info_Full.csv`: Source data for restaurants (migrated to database)
- `Reviews.csv`: Source data for reviews (migrated to database)

**Missing/Legacy Data Files** (referenced in code but may not exist):
- `Travel_dataset.csv`: Historical travel records (legacy)
- `country_info.csv`: Country-level metrics (legacy)
- `Attractions.csv`: Tourist attractions by country (legacy)
- `booking_reviews copy.csv`: Backup or alternative review data

### Test and Utility Scripts

**Test Scripts** - Standalone Dash apps for component testing:
- `test_restaurant_barChart.py`: Interactive testing of restaurant rating visualizations with dropdown filters
- `test_rating_distribution.py`: Analysis of rating distributions across restaurants
- `test_reviews_join.py`: Validates proper joining of restaurant and review data
- `test_login_page.py`: Tests authentication page components and styling
- `test.py`, `test2.py`: Additional test scripts

**Data Generation Scripts**:
- `generate_reviews.py`: Generates synthetic review data for restaurants
- `change_totalRating.py`: Calculates and updates restaurant total ratings from reviews
- `restore_prices_and_add_price_category.py`: Processes restaurant pricing data and categorization
- `combine.py`: Data combination utility (purpose unclear)

### URL Routing and Page Navigation

The app uses three main pages with URL-based routing:

1. **Homepage** (`/`):
   - Hero section with search bar
   - Random selection of 10 top-rated restaurants (4-5 stars)
   - Tab navigation (Saved/Wishlisted/Favorites)
   - Inspiration grid
   - Search preview (shows first few results)

2. **Restaurant List Page** (`/restaurants` - triggered by view-mode state):
   - Full paginated grid (12 per page)
   - Advanced search with all filters active
   - Database queries via `search_restaurants()` function
   - Pagination controls at bottom
   - Each card clickable to navigate to detail page

3. **Restaurant Detail Page** (`/restaurant/<restaurant_id>`):
   - URL parsing extracts restaurant ID from pathname
   - Database query fetches full restaurant data via `get_restaurant_by_id()`
   - Displays: header with name/rating, image gallery, pricing, location, categories, reviews
   - Interactive rating distribution bar chart (click to filter reviews)
   - Back button with state preservation (returns to previous page)
   - Error handling for invalid/missing restaurant IDs

**Routing Implementation**:
- Uses `dcc.Location` component for URL tracking
- Pattern matching callbacks handle dynamic card clicks
- State stores track previous page location for proper back navigation
- URL changes trigger page re-renders via callback chain

### Key Data Flow

1. **Authentication**:
   - App loads → check `session-store` → validate session → route to login or main app (`create_main_layout()`)
   - Login: verify credentials → create session (UUID) → store in database and session storage
   - Logout: delete session from database → clear session storage → redirect to login
   - Register: validate inputs → hash password (SHA-256) → store in database → show success message

2. **Data Loading** (DATABASE ARCHITECTURE):
   - **On first run**: Execute `migrate_to_db.py` to create `restaurants.db` from CSV files
   - **App startup**: Import `utils/database.py` module (no CSV loading, only connection string)
   - **On-demand queries**: All data fetched via SQL queries with proper indexing
   - **Benefits**:
     - Faster startup (no CSV parsing on every app launch)
     - Efficient filtering (SQL WHERE clauses with indexes)
     - Lower memory usage (query only what's needed, not full dataset)
     - Better scalability (performance doesn't degrade with data size)
     - Concurrent access support

3. **Restaurant Display Flow**:
   - **Homepage**: On page load → `get_random_top_restaurants(10)` → display in card grid
   - **Search**: User inputs filters → `search_restaurants()` with SQL parameters → results to store → display matches
   - **List Page**: Initialize with all restaurants → paginate → display 12 per page
   - **Detail Page**: Extract ID from URL → `get_restaurant_by_id(id)` → render detail layout
   - **Tab Navigation**: Switch between saved trips, wishlisted hotels, favorite restaurants (UI only, backend pending)

4. **Search & Filter Flow**:
   - User types keyword → debounce 300ms → generate suggestions → display dropdown
   - User selects filter → update active filter chips → trigger search
   - Search executes → SQL query with all active filters → update results store
   - Results store change → update grid display and pagination
   - Search saved to history (session storage) and popular searches (local storage)

5. **Legacy Features** (not in current UI but code exists):
   - Trip Planner: User inputs → filters → scoring → sorted table
   - Attractions: Country selection → geocoding → map display

### Callback Architecture

The app uses over 30 callbacks organized by functionality. Key callbacks include:

**Authentication Callbacks** (6 callbacks):
- Page routing: Routes user to login/register/main app based on session state and `page-mode`
- `switch_to_register()` / `switch_to_login()`: Toggle between login and register pages
- Login handler: Validates credentials, creates session (2 hours or 30 days), updates session storage
- Register handler: Validates inputs (6+ char password, matching confirmation) and creates new user
- Logout handlers: Three separate callbacks for logout from home, restaurant list, and detail pages

**Navigation Callbacks** (4 callbacks):
- `navigate_to_restaurant_list()`: Navigate from home to restaurant list page
- Back button handler: Returns to previous page with proper state management
- Navigation trigger: Handles back button clicks using pattern matching
- View mode updater: Listens to navigation trigger and updates view mode

**User Dropdown Callbacks** (3 callbacks):
- Toggle dropdown on home page
- Toggle dropdown on restaurant list page
- Toggle dropdown on detail page

**Homepage UI Callbacks** (3 callbacks):
- `populate_destinations_cards()`: Loads random 4-5 star restaurants on page load
- Tab navigation: Switches between Saved Trips/Wishlisted/Favorites tabs
- `populate_inspiration_grid()`: Loads inspiration article cards

**Search & Filter Callbacks** (10+ callbacks):
- Search suggestions display (real-time as user types)
- Advanced filters toggle
- Clear all filters
- Cuisine dropdown toggle (with mutual exclusivity)
- Rating dropdown toggle (with mutual exclusivity)
- Cuisine option selection
- Rating option selection
- Active filter chips display
- Search button handler (home page preview)
- Search handler (restaurant list page with database queries)

**Restaurant List Page Callbacks** (3 callbacks):
- Initialize restaurant list: Loads all restaurants on page entry
- Update restaurant grid: Displays paginated results (12 per page)
- Pagination handler: Updates current page using pattern matching callbacks

**Restaurant Detail Page Callbacks** (8 callbacks):
1. Route detector: Parses restaurant ID from URL
2. Data loader: Fetches restaurant data from database
3. Content renderer: Renders detail page layout
4. Card click handler: Navigates to detail page when card is clicked (pattern matching)
5. Back button handler: Returns to previous page
6. Error back button: Handles errors and returns to home
7. User dropdown toggle (detail page)
8. Logout from detail page
9. Reviews bar chart click: Filters reviews by rating when clicking bar chart

**Key Technical Details**:
- **Pattern Matching**: Used extensively for dynamic elements (restaurant cards, pagination buttons, back buttons)
- **State Management**: Multiple dcc.Store components track session, page mode, view mode, dropdown state, search results, pagination
- **Prevent Update**: Most callbacks use `prevent_initial_call=True` or `PreventUpdate` to avoid unnecessary triggers
- **Allow Duplicate**: Many outputs use `allow_duplicate=True` to enable multiple callbacks updating same component
- **Database Integration**: Search and detail callbacks query SQLite database on-demand instead of filtering in-memory DataFrames

**Legacy Callbacks** (Code exists but not in current UI):
- Overview page: Bar/pie/map/box chart updates
- Trip Planner: Table filtering and country comparison charts
- Attractions: Country selection and map display
- Hamburger menu navigation

### Scoring Algorithm (Legacy Trip Planner)

**Note**: This algorithm exists in `utils/data_transform.py` but is not used in the current restaurant-focused UI.

1. CPI adjustment normalizes accommodation costs across countries
2. Safety Index and adjusted cost are MinMax normalized to 0-1
3. Cost score is inverted (lower cost = higher score)
4. Final score = weighted average × 100, with weights normalized if both are non-zero
5. Countries sorted by: Score (desc), Safety Index (desc), adjusted cost (asc)

## Important Notes

**Current Application State**:
- **UI Focus**: App currently implements a modern restaurant discovery platform (Voyage), not the legacy travel analysis dashboard
- **Data Source**: SQLite database with 2000+ Kyoto restaurants (migrated from CSV)
- **Legacy Code**: Many utility functions in `utils/` are unused by current implementation (see Legacy Code section)
- **Active Development**: Search, filtering, pagination, and detail pages are fully functional; personalized features (saved/wishlisted) have UI but no backend yet

**Authentication & Security**:
- **Login Required**: Application requires login on startup. Test accounts: `admin`/`admin123` and `demo`/`demo123`
- **Session Management**: SQLite sessions with 2-hour expiry (or 30 days with "remember me")
- **Password Security**: Uses SHA-256 hashing (consider bcrypt/argon2 for production)
- **Database Auto-Init**: `users.db` auto-created on first run by `auth.py` module import
- **Test Accounts**: Created automatically if database is new (admin/admin123, demo/demo123)

**Technical Details**:
- **Theme**: Dark theme with gold accent (`#deb522`) consistent across all pages
- **External Resources**: FontAwesome 6.4.0 icons, Bootstrap theme, Plotly dark template
- **State Management**: Uses `dcc.Store` with multiple storage types:
  - `'session'`: Auth session, search history, page mode
  - `'memory'`: View mode, dropdown state, search results, pagination
  - `'local'`: Popular searches (persistent across sessions)
- **Pagination**: 12 restaurants per page with dynamic pagination controls
- **Image Assets**: `Hazuki.jpg` used as hero background and placeholder for all card images

## Important Implementation Patterns

**Pattern Matching Callbacks**:
The app extensively uses Dash's pattern matching callbacks (ALL, MATCH) for dynamic elements:
```python
Input({'type': 'restaurant-card', 'index': ALL}, 'n_clicks')
Input({'type': 'page-btn', 'index': ALL}, 'n_clicks')
Input({'type': 'back-btn', 'index': ALL}, 'n_clicks')
```
This allows handling clicks on dynamically generated cards, pagination buttons, and back buttons without hardcoding callback for each element.

**State Store Strategy**:
- `session-store`: User authentication session ID (validated on each page load)
- `page-mode`: Controls login/register/main app routing
- `view-mode`: Controls home/restaurant-list page display
- `dropdown-open`: Tracks user dropdown menu state (separate for each page)
- `search-results-store`: Holds current search results as list of dicts
- `current-page-store`: Tracks pagination current page number
- `search-params-store`: Stores active search parameters for re-querying
- `selected-restaurant-id`: Holds ID of restaurant to display in detail page
- `restaurant-detail-data`: Cached restaurant data for detail page

**Database Query Pattern**:
All database queries use context manager for automatic connection handling:
```python
with get_db_connection() as conn:
    query = "SELECT * FROM restaurants WHERE ..."
    df = pd.read_sql_query(query, conn, params=params)
```
This ensures connections are properly closed even if errors occur.

**Search Debouncing**:
Search input uses `debounce=300` (300ms) to avoid excessive queries while user is typing.

**Legacy Features** (code exists but unused):
- Geopy geocoding for attractions mapping
- Country code mapping for choropleth maps (23 countries)
- Alert ranking system (灰色=2, 黃色=3, 橙色=4)
- Trip planner scoring algorithm with CPI adjustment
- Hamburger menu navigation system

## Troubleshooting

**Database Issues**:
- **"No such table: restaurants"**: Run `python migrate_to_db.py` to create the database from CSV files
- **Database locked errors**: Only one process can write to SQLite at a time. Ensure only one app instance is running
- **Slow search performance**: Check that indexes were created properly during migration. Re-run `migrate_to_db.py` if needed
- **Missing restaurant data**: Verify `./data/Kyoto_Restaurant_Info_Full.csv` exists before running migration

**Authentication Issues**:
- **Session not persisting**: Verify `session-store` uses `storage_type='session'` not `'memory'`
- **Can't login with test accounts**: Check that `./data/users.db` was created. Delete it and restart app to recreate with test accounts
- **Session expires too quickly**: Default is 2 hours. Check "Remember me" checkbox for 30-day sessions

**UI/Display Issues**:
- **Restaurant cards not showing**: Check browser console for errors. Verify database has data (`python performance_test.py`)
- **Images not displaying**: Ensure `assets/Hazuki.jpg` and `assets/logo.png` exist
- **Search not working**: Check browser console for callback errors. Verify all filter inputs have proper IDs
- **Pagination not working**: Check `current-page-store` and `search-results-store` in browser DevTools
- **Detail page shows error**: Verify restaurant ID in URL is valid. Check database has restaurant with that ID

**Callback Issues**:
- **PreventUpdate errors**: Check that all inputs exist in layout before callbacks fire
- **Circular callback errors**: Verify `allow_duplicate=True` is used when multiple callbacks update same output
- **Pattern matching not working**: Ensure dictionary IDs have exact same keys in layout and callback

**Performance Issues**:
- **App slow to start**: This is normal for Dash. Database mode should be faster than CSV loading
- **Search takes too long**: Check SQL query performance. Consider adding more indexes if filtering by new columns
- **Too many callbacks firing**: Use `prevent_initial_call=True` to avoid unnecessary updates

**Legacy Feature Issues** (if trying to use old features):
- **Missing CSV files**: Legacy code references `Travel_dataset.csv`, `country_info.csv`, and `Attractions.csv` which may not exist
- **Geocoding failures**: Attractions page requires internet connection for Nominatim API
- **Charts not updating**: Legacy callbacks may reference missing data or `dcc.Store` components
- **Menu not appearing**: Hamburger menu CSS and callbacks exist but are not integrated in current UI
