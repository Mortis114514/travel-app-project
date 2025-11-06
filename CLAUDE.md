# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Dash web application called "Voyage" - a modern restaurant discovery and travel planning platform with integrated user authentication. The application features:
- **Modern Homepage**: Hero section with background image, search functionality, and curated restaurant recommendations
- **Restaurant Discovery**: Browse top-rated restaurants (4-5 stars) from Kyoto with ratings, categories, and locations
- **Personalized Content**: Saved trips, wishlisted hotels, and favorite restaurants organized by tabs
- **Inspiration Section**: Travel articles and guides organized in a grid layout
- **Search System**: Multi-criteria search by destination, cuisine type, and rating

The application includes a complete authentication system with login, registration, session management (SQLite-based), and page access protection. The UI uses a dark theme with gold accent color (#deb522) and modern card-based layouts.

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
- **UI**: Modern "Voyage" homepage with hero section, search bar, restaurant cards
- **Data**: Only uses `Kyoto_Restaurant_Info_Full.csv` for restaurants
- **Features**: Restaurant search/filter, user authentication, tab navigation
- **Callbacks**: Focus on UI interactions (dropdown, tabs, search, cards)
- **Style**: `voyage_styles.css` for modern card-based layouts

### Legacy Code (still in codebase but unused)
- **UI**: Multi-tab dashboard (Overview/Trip Planner/Attractions) with hamburger menu
- **Data**: Travel datasets, country info, attractions, safety metrics
- **Features**: Data visualizations (bar/pie/map/box), trip scoring, geocoding
- **Utils**: `data_transform.py`, `data_clean.py`, `visualization.py` functions
- **Style**: `gear_menu.css`, `login_styles.css`

**When modifying code**: Check if you're working with current features (restaurant homepage) or legacy features (travel analysis). Many functions in `utils/` are no longer called by `app.py`.

## Architecture

### Main Application (`app.py`)
- Initializes Dash app with Bootstrap styling and custom CSS (`voyage_styles.css`)
- **Loads data from SQLite database** (`./data/restaurants.db`) instead of CSV files for better performance
  - Uses `utils/database.py` module for all data queries
  - On first run, execute `python migrate_to_db.py` to create the database
- Implements authentication system with login/logout/register callbacks
- Uses `dcc.Store` for session management (`session-store`), page mode (`page-mode`), current page tracking, dropdown state
- Creates modern homepage layout with hero section, search bar, restaurant cards, tabs, and inspiration grid
- Routes users to login page or main app based on session validation
- Key UI components: `create_destination_card()`, `create_saved_trip_card()`, `create_add_new_card()`, `create_inspiration_card()`, `create_compound_search_bar()`

### Utils Package (`utils/`)

**Note**: Most utilities are designed for legacy travel analysis features. Current app.py uses primarily `auth.py` for authentication.

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

**`database.py`**: Restaurant data access layer (NEW - actively used)
- `get_all_restaurants()`: Fetch all restaurants with optional sorting
- `get_random_top_restaurants()`: Get random high-rated restaurants
- `search_restaurants()`: Advanced search with keyword, cuisine, rating, price, station filters
- `get_unique_stations()`: Get list of all unique station names
- `get_unique_cuisines()`: Get list of all unique cuisine types
- `get_restaurant_by_id()`: Fetch single restaurant by ID
- `get_top_rated_restaurants()`: Get highest rated restaurants with minimum review threshold
- `get_restaurants_by_category()`: Filter by rating category
- Database location: `./data/restaurants.db`
- All queries use SQL with proper indexing for optimal performance

### Pages Package (`pages/`)

**`login_page.py`**: UI components for authentication
- `create_login_layout()`: Login page with username/password form, "remember me" checkbox, and registration link
- `create_register_layout()`: Registration page with username, email, password, and password confirmation fields
- Both layouts use consistent dark theme with gold accent (`#deb522`)
- Requires `assets/login_styles.css` for custom styling

### Assets Package (`assets/`)

Contains static resources for the application:
- `voyage_styles.css`: Main application styles for modern homepage layout
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

### Key Data Flow

1. **Authentication**:
   - App loads → check `session-store` → validate session → route to login or main app (`create_main_layout()`)
   - Login: verify credentials → create session (UUID) → store in database and session storage
   - Logout: delete session from database → clear session storage → redirect to login
   - Register: validate inputs → hash password (SHA-256) → store in database → show success message

2. **Data Loading** (NEW DATABASE ARCHITECTURE):
   - **On first run**: Execute `migrate_to_db.py` to create `restaurants.db` from CSV files
   - **App startup**: Import `utils/database.py` module (no CSV loading)
   - **On-demand queries**: All data fetched via SQL queries with proper indexing
   - **Benefits**:
     - Faster startup (no CSV parsing)
     - Efficient filtering (SQL WHERE clauses with indexes)
     - Lower memory usage (query only what's needed)
     - Better scalability (performance doesn't degrade with data size)

3. **Restaurant Display** (Current Homepage):
   - On page load → `get_random_top_restaurants(10)` → filter 4-5 star restaurants → display in card grid
   - User searches → filter by destination/cuisine/rating → display matching restaurants
   - Tab navigation → switch between saved trips, wishlisted hotels, favorite restaurants

4. **Legacy Features** (not in current UI but code exists):
   - Trip Planner: User inputs → filters → scoring → sorted table
   - Attractions: Country selection → geocoding → map display

### Callback Architecture

**Authentication Callbacks**:
- `display_page()`: Routes user to login/register/main app based on session state and `page-mode`
- `login()`: Validates credentials, creates session (2 hours or 30 days), updates session storage
- `logout_from_dropdown()`: Deletes session when user clicks logout in dropdown menu
- `register()`: Validates inputs (6+ char password, matching confirmation) and creates new user
- `switch_to_register()` / `switch_to_login()`: Toggle between login and register pages

**Homepage UI Callbacks** (Current Implementation):
- `toggle_user_dropdown()`: Opens/closes user avatar dropdown menu
- `populate_destinations_cards()`: Loads random 4-5 star restaurants on page load
- `handle_tab_navigation()`: Switches between Saved Trips/Wishlisted/Favorites tabs
- `populate_inspiration_grid()`: Loads inspiration article cards
- `handle_search()`: Filters restaurants by destination, cuisine, and rating criteria

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
- **Data Mismatch**: Code references travel CSV files that may not exist. App works with restaurant data only
- **Legacy Code**: Many utility functions in `utils/` are unused by current homepage implementation

**Authentication & Security**:
- **Login Required**: Application requires login on startup. Test accounts: `admin`/`admin123` and `demo`/`demo123`
- **Session Management**: SQLite sessions with 2-hour expiry (or 30 days with "remember me")
- **Password Security**: Uses SHA-256 hashing (consider bcrypt/argon2 for production)
- **Database Auto-Init**: `users.db` auto-created on first run by `auth.py` module import
- **Test Accounts**: Created automatically if database is new (admin/admin123, demo/demo123)

**Technical Details**:
- **Theme**: Dark theme with gold accent (`#deb522`) consistent across all pages
- **External Resources**: FontAwesome 6.4.0 icons, Bootstrap theme, Plotly dark template
- **State Management**: Uses `dcc.Store` with `storage_type='session'` for auth, `'memory'` for UI state
- **Restaurant Filtering**: Filters by `Rating_Category == '4~5 星餐廳'` for top recommendations
- **Image Assets**: `Hazuki.jpg` used as hero background and placeholder for all card images

**Legacy Features** (code exists but unused):
- Geopy geocoding for attractions mapping
- Country code mapping for choropleth maps (23 countries)
- Alert ranking system (灰色=2, 黃色=3, 橙色=4)
- Trip planner scoring algorithm with CPI adjustment
- Hamburger menu navigation system

## Troubleshooting

**Common Issues**:
- **Missing CSV files**: If app crashes on startup, check that `Travel_dataset.csv`, `country_info.csv`, and `Attractions.csv` exist in `data/` folder, or comment out their loading in `app.py` lines 43-45
- **Database locked errors**: Only one process can write to SQLite at a time. Ensure only one app instance is running
- **Session not persisting**: Verify `session-store` uses `storage_type='session'` not `'memory'`
- **Restaurant cards not showing**: Check that `Kyoto_Restaurant_Info_Full.csv` exists and has `Rating_Category` column with '4~5 星餐廳' values
- **Images not displaying**: Ensure `assets/Hazuki.jpg` and `assets/logo.png` exist

**Legacy Feature Issues** (if trying to use old features):
- **Geocoding failures**: Attractions page requires internet connection for Nominatim API
- **Charts not updating**: Legacy callbacks may reference missing data or `dcc.Store` components
- **Menu not appearing**: Hamburger menu CSS and callbacks exist but are not integrated in current UI
