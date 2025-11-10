# GEMINI.md - Project Guide

This guide provides a comprehensive overview of the "Voyage" Dash application for effective collaboration and development. It is based on detailed analysis of the project structure and documentation.

## 1. Project Overview

This is a Python-based **Plotly Dash web application** for discovering restaurants in Kyoto. The project has evolved from a legacy travel analysis tool into a modern, database-driven restaurant discovery platform.

-   **Primary Goal**: Allow users to search, filter, and view detailed information about 2,000+ Kyoto restaurants.
-   **Core Technologies**: Python, Plotly Dash, Dash Bootstrap Components, Pandas.
-   **Data Backend**: **SQLite**. The app uses a dedicated database (`data/restaurants.db`) for restaurant data and another (`data/users.db`) for user authentication. This is a significant improvement over the legacy CSV-based approach.
-   **Key Features**:
    -   User authentication (register, login, sessions).
    -   An interactive homepage with an advanced search bar and curated content.
    -   A paginated restaurant list page with multi-criteria filtering (keyword, cuisine, rating, price, location).
    -   Detailed restaurant pages with image galleries, maps, and review analysis.
    -   Real-time UI features like search suggestions and filter chips.

## 2. Development Commands

**First-Time Setup:**
```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database from source CSVs (IMPORTANT)
python migrate_to_db.py
```

**Running the Application:**
```bash
# Run the main Dash app
python app.py
```
The application will be available at `http://127.0.0.1:8050`. It runs in `debug=True` mode by default.

**Testing & Utilities:**
```bash
# Test database query performance
python performance_test.py

# Test individual components (these are standalone Dash apps)
python test_restaurant_barChart.py
python test_login_page.py
```

## 3. Architecture Summary

**IMPORTANT: Current vs. Legacy Code**
The codebase is in transition. The main `app.py` file runs the **current restaurant discovery platform**. However, many files in `utils/` (like `data_clean.py`, `data_transform.py`) contain code for a **legacy travel analysis dashboard** and are no longer actively used by `app.py`.

**Key Directories & Modules:**

-   `app.py`: **(Active)** The main application entry point. Defines layouts, initializes the app, and contains most of the callback logic.
-   `data/`:
    -   `restaurants.db`: **(Active)** Primary SQLite database for all restaurant data.
    -   `users.db`: **(Active)** SQLite database for user and session management.
    -   `*.csv`: Source data, used only for the `migrate_to_db.py` script.
-   `utils/`:
    -   `database.py`: **(Active)** The data access layer. Contains all SQL query functions for restaurants. **This is the preferred way to fetch data.**
    -   `auth.py`: **(Active)** Manages user creation, login, and session handling.
    -   `visualization.py`, `data_transform.py`, etc.: **(Mostly Legacy)** Contain functions for the old travel dashboard.
-   `components/` & `callbacks/`:
    -   `enhanced_search.py`: **(Active)** Defines the UI and helper functions for the advanced search bar.
    -   `search_callbacks.py`: **(Active)** Contains callbacks specifically for the search functionality.
-   `pages/`:
    -   `login_page.py`: **(Active)** Defines the UI for the login and registration pages.
-   `assets/`:
    -   `voyage_styles.css`: **(Active)** Main stylesheet for the current restaurant application.
    -   `enhanced_search_styles.css`: **(Active)** Styles for the search components.
    -   `login_styles.css`, `gear_menu.css`: **(Legacy)** Styles for old components.

## 4. Core Workflows

**Authentication Flow:**
1.  On app load, a callback checks for a valid session ID in `dcc.Store(id='session-store', storage_type='session')`.
2.  The session ID is validated against the `sessions` table in `users.db`.
3.  If valid, the main app layout is rendered. If not, the user is directed to the login page.
4.  Passwords are SHA-256 hashed. Test accounts (`admin`/`demo`) are created automatically if `users.db` is new.

**Data & Search Flow:**
1.  The app **does not** load CSVs into memory on startup.
2.  When a user performs a search, the callback in `app.py` or `search_callbacks.py` is triggered.
3.  This callback calls a function from `utils/database.py` (e.g., `search_restaurants()`).
4.  The database function constructs and executes a parameterized SQL query against `restaurants.db`.
5.  The results are returned as a Pandas DataFrame, converted to a dictionary, and stored in a `dcc.Store`.
6.  A separate callback listens for changes to this store and updates the UI (e.g., the restaurant grid).

## 5. Key Implementation Patterns

-   **Database over In-Memory Pandas**: To ensure performance and scalability, always prefer adding a new query function to `utils/database.py` instead of loading a large DataFrame and filtering it with Pandas inside a callback.
-   **Pattern-Matching Callbacks**: The app uses `ALL` and `MATCH` extensively to handle dynamically generated components like restaurant cards, pagination buttons, and filter chips. This is a core pattern for interactivity.
-   **State Management with `dcc.Store`**: Application state is managed across multiple stores with different persistence types:
    -   `storage_type='session'`: For user session data and search history.
    -   `storage_type='memory'`: For data that doesn't need to persist across page reloads (e.g., search results).
    -   `storage_type='local'`: For data that should persist long-term in the browser (e.g., popular searches).
-   **Modular Callbacks**: While many callbacks are in `app.py`, newer features like the search bar have their callbacks separated into their own files (e.g., `callbacks/search_callbacks.py`), which is a good practice to follow.