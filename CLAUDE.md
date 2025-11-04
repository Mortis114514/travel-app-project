# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Dash web application for travel data analysis and trip planning with integrated user authentication. The application provides an interactive dashboard with three main sections accessed via a hamburger menu (gear icon):
- **Overview**: Visualizations of travel patterns, safety metrics, and costs by country/continent
- **Trip Planner**: A recommendation system for destinations based on budget, safety, accommodation preferences, and visa requirements
- **Attractions**: Geographic display of tourist attractions by country

The application includes a complete authentication system with login, registration, session management, and page access protection. Navigation between pages is handled by a custom hamburger menu in the top-right corner.

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

The app runs on default Dash port (usually http://127.0.0.1:8050). Set `debug=True` in `app.run()` for development mode.

## Architecture

### Main Application (`app.py`)
- Initializes Dash app with Bootstrap styling
- Loads and preprocesses three CSV datasets from `./data/`:
  - `Travel_dataset.csv`: Historical travel records with traveler demographics and costs
  - `country_info.csv`: Country-level data (CPI, PCE, Safety Index, Travel Alerts, Visa info)
  - `Attractions.csv`: Tourist attractions by country
- Implements authentication system with login/logout/register callbacks
- Uses `dcc.Store` for session management (`session-store`) and cross-callback state management
- Defines multi-tab layout with callbacks for each page
- Routes users to login page or main app based on session validation

### Utils Package (`utils/`)

**`const.py`**: Constants and configuration
- `ALERT_RANK_MAP`: Travel alert severity mapping (灰色=2, 黃色=3, 橙色=4)
- `ALL_COMPARE_METRICS`: List of metrics for country comparison charts
- `TAB_STYLE`: UI styling for tab components
- `get_constants()`: Computes dashboard statistics (countries, travelers, nationalities, avg days)

**`data_clean.py`**: Data cleaning pipeline
- `travel_data_clean()`: Converts cost strings to float, parses dates, creates age groups and monthly bins
- `countryinfo_data_clean()`: Removes null values from country info
- `data_merge()`: Left joins travel data with country info on 'Destination'

**`data_transform.py`**: Business logic and filtering
- `preprocess_travel_df()`: Calculates daily/trip accommodation costs (`acc_daily_cost`, `acc_trip_cost`)
- `filter_by_cost_and_types()`: Filters by accommodation cost range and types
- `pick_country_level()`: Aggregates trip-level data to country-level using first non-null values
- `filter_by_alert_and_visa()`: Applies travel alert threshold and visa-exempt filtering
- `compute_scores()`: Calculates weighted scores (0-100) combining safety and cost metrics using CPI adjustment and MinMax normalization
- `prepare_country_compare_data()`: Prepares data for radar/bar/line comparison charts (max 5 countries)

**`data_validation.py`**: Helper utilities
- `is_exempt()`: Validates visa exemption status from various input formats
- `minmax()`: MinMax normalization (0-1 range) with edge case handling
- `fmt()`: Number formatting for display

**`visualization.py`**: Plotly chart generation
- `build_compare_figure()`: Creates radar/bar/line charts for country comparisons with MinMax normalization
- `generate_bar()`, `generate_pie()`, `generate_map()`, `generate_box()`: Overview page visualizations
- `build_table_component()`: Creates sortable/filterable Dash DataTable for trip planner results
- `generate_stats_card()`: Top-level statistics cards with icons
- All charts use dark theme (`plotly_dark`) with golden accent color (`#deb522`)

**`auth.py`**: Authentication and user management
- `init_db()`: Initializes SQLite database with users and sessions tables
- `create_user()`: Creates new user with hashed password (SHA-256)
- `verify_user()`: Validates username/password and updates last login time
- `create_session()`: Creates new session with expiration time
- `get_session()`: Retrieves and validates session by ID
- `delete_session()`: Removes session (logout)
- `clean_expired_sessions()`: Removes expired sessions from database
- Database location: `./data/users.db`

### Pages Package (`pages/`)

**`login_page.py`**: UI components for authentication
- `create_login_layout()`: Login page with username/password form, "remember me" checkbox, and registration link
- `create_register_layout()`: Registration page with username, email, password, and password confirmation fields
- Both layouts use consistent dark theme with gold accent (`#deb522`)
- Requires `assets/login_styles.css` for custom styling

### Assets Package (`assets/`)

Contains static resources for the application:
- `login_styles.css`: Authentication page styles
- `gear_menu.css`: Hamburger menu navigation styles
- `logo.png`, `earth.svg`, `user.svg`, `calendar.svg`: UI icons and branding
- `bg_hamburger.png`: Background for menu button

### Key Data Flow

1. **Authentication**:
   - App loads → check session storage → validate session → route to login or main app
   - Login: verify credentials → create session (UUID) → store in database and session storage
   - Logout: delete session from database → clear session storage → redirect to login
   - Register: validate inputs → hash password → store in database → redirect to login

2. **Data Loading**: CSVs → `travel_data_clean()` / `countryinfo_data_clean()` → `data_merge()` → `df_merged`

3. **Trip Planner**:
   - User inputs (cost, types, alerts, visa, weights) → `filter_by_cost_and_types()` → `pick_country_level()` → `filter_by_alert_and_visa()` → `compute_scores()` → sorted table + top 5 for comparison

4. **Attractions**: Selected country → filter `attractions_df` → geopy geocoding → Leaflet map with markers

### Callback Architecture

- **Authentication Callbacks**:
  - `display_page()`: Routes user to login/register/main app based on session state and page mode
  - `login()`: Validates credentials, creates session, updates session storage
  - `logout_from_menu()`: Deletes session and clears session storage (triggered from hamburger menu)
  - `register()`: Validates inputs and creates new user account
  - `switch_to_register()` / `switch_to_login()`: Toggle between login and register pages

- **Navigation Callbacks** (Hamburger Menu):
  - `toggle_menu()`: Opens/closes the hamburger menu
  - `update_menu_display()`: Updates CSS classes for menu visibility and animation
  - `navigate_page()`: Switches between Overview/Trip Planner/Attractions pages
  - `update_menu_active_state()`: Highlights the current active page in menu
  - All navigation state stored in `dcc.Store` components (`menu-open`, `current-page`)

- **Overview Page**: Four independent callbacks for bar/pie/map/box charts, each triggered by dropdown changes

- **Trip Planner Page**:
  - Main callback returns both table component and top 5 countries to `dcc.Store`
  - Comparison callback reads from `dcc.Store` to generate radar/bar/line charts

- **Attractions Page**: Single callback with `prevent_initial_call=True` and `State` for country selection

### Scoring Algorithm (Trip Planner)

1. CPI adjustment normalizes accommodation costs across countries
2. Safety Index and adjusted cost are MinMax normalized to 0-1
3. Cost score is inverted (lower cost = higher score)
4. Final score = weighted average × 100, with weights normalized if both are non-zero
5. Countries sorted by: Score (desc), Safety Index (desc), adjusted cost (asc)

## Important Notes

- **Authentication**: Application requires login on startup. Default test accounts: `admin`/`admin123` and `demo`/`demo123`
- **Session Management**: Sessions stored in SQLite (`data/users.db`). Default expiry: 2 hours (normal) or 30 days (remember me)
- **Password Security**: Uses SHA-256 hashing (consider bcrypt/argon2 for production)
- **Database**: SQLite database (`users.db`) auto-created on first run with two tables: `users` and `sessions`. Default admin accounts created automatically by `auth.py` on initialization
- **First Run**: On first run, `auth.py` creates the database and initializes test accounts. If database exists, it safely skips account creation
- **Geopy Rate Limiting**: `RateLimiter(min_delay_seconds=1)` prevents API throttling when geocoding attractions
- **Country Code Mapping**: `visualization.py` contains hardcoded ISO country code mapping for choropleth maps (23 countries mapped to ISO 3166 codes)
- **Alert Ranking**: Lower numbers = safer (灰色=2 is safer than 橙色=4) as defined in `ALERT_RANK_MAP`
- **Month Ordering**: Bar charts use predefined month order array for correct chronological display
- **Bootstrap Theme**: Uses `dbc.themes.BOOTSTRAP` for responsive layout
- **Color Scheme**: Gold/black theme (`#deb522` / `black`) used consistently across UI and authentication pages
- **External Resources**: FontAwesome 6.4.0 icons loaded from CDN for UI elements
- **Page Navigation**: Uses `dcc.Store` components with `storage_type='memory'` for in-session state (menu, page routing)

## Troubleshooting

- **Database locked errors**: Only one process can write to SQLite at a time. Ensure only one app instance is running
- **Geocoding failures**: Attractions page uses Nominatim API. If attractions don't appear, check internet connectivity and rate limiting
- **Session not persisting**: Check that `session-store` uses `storage_type='session'` not `'memory'`
- **Menu not appearing**: Verify `assets/gear_menu.css` is loaded and no CSS conflicts exist
- **Charts not updating**: Ensure callbacks check `current-page` data to prevent unnecessary updates on inactive tabs
