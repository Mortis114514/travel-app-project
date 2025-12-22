"""
Callbacks for the new drag-and-drop Create Trip page
These will be added to app.py
"""

# ===== CALLBACK 1: Populate Draggable Favorites =====
@app.callback(
    Output('draggable-favorites-container', 'children'),
    [Input('session-store', 'data'),
     Input({'type': 'fav-filter', 'category': ALL}, 'n_clicks')],
    [State({'type': 'fav-filter', 'category': ALL}, 'id')],
    prevent_initial_call=False
)
def populate_draggable_favorites(session_data, filter_clicks, filter_ids):
    """Load and display draggable favorite items"""
    from utils.favorites import get_user_favorites
    from utils.auth import get_session
    from dash import callback_context

    # Determine active filter
    active_category = 'all'
    ctx = callback_context
    if ctx.triggered and 'fav-filter' in ctx.triggered[0]['prop_id']:
        triggered_id = ctx.triggered_id
        if triggered_id:
            active_category = triggered_id['category']

    # Get user ID
    if not session_data or 'session_id' not in session_data:
        return html.Div("Please log in to see your favorites.", style={'padding': '2rem', 'textAlign': 'center', 'color': '#888'})

    user_id = get_session(session_data['session_id'])
    if not user_id:
        return html.Div("Session expired. Please log in again.", style={'padding': '2rem', 'textAlign': 'center', 'color': '#888'})

    # Get favorites
    all_favorites = get_user_favorites(user_id)
    if not all_favorites:
        return html.Div([
            html.I(className='fas fa-heart', style={'fontSize': '3rem', 'color': '#ddd', 'marginBottom': '1rem'}),
            html.P("No favorites yet", style={'color': '#888'}),
            html.P("Add favorites from restaurant, hotel, or attraction pages", style={'color': '#aaa', 'fontSize': '0.85rem'})
        ], style={'textAlign': 'center', 'padding': '3rem'})

    # Filter by category
    if active_category != 'all':
        favorites = [f for f in all_favorites if f['item_type'] == active_category]
    else:
        favorites = all_favorites

    if not favorites:
        return html.Div(f"No {active_category}s in your favorites", style={'padding': '2rem', 'textAlign': 'center', 'color': '#888'})

    # Create draggable items
    return [create_draggable_favorite_item(fav) for fav in favorites]


# ===== CALLBACK 2: Update Filter Button Styles =====
@app.callback(
    [Output({'type': 'fav-filter', 'category': 'all'}, 'className'),
     Output({'type': 'fav-filter', 'category': 'restaurant'}, 'className'),
     Output({'type': 'fav-filter', 'category': 'hotel'}, 'className'),
     Output({'type': 'fav-filter', 'category': 'attraction'}, 'className')],
    [Input({'type': 'fav-filter', 'category': ALL}, 'n_clicks')],
    [State({'type': 'fav-filter', 'category': ALL}, 'id')],
    prevent_initial_call=True
)
def update_filter_styles(n_clicks, filter_ids):
    """Update active filter chip styling"""
    from dash import callback_context

    ctx = callback_context
    if not ctx.triggered:
        return ['filter-chip active-filter', 'filter-chip', 'filter-chip', 'filter-chip']

    triggered_id = ctx.triggered_id
    if not triggered_id:
        return ['filter-chip active-filter', 'filter-chip', 'filter-chip', 'filter-chip']

    active_category = triggered_id['category']

    return [
        'filter-chip active-filter' if active_category == 'all' else 'filter-chip',
        'filter-chip active-filter' if active_category == 'restaurant' else 'filter-chip',
        'filter-chip active-filter' if active_category == 'hotel' else 'filter-chip',
        'filter-chip active-filter' if active_category == 'attraction' else 'filter-chip'
    ]


# ===== CALLBACK 3: Populate Timeline Based on Dates =====
@app.callback(
    Output('trip-timeline-container', 'children'),
    [Input('trip-start-date', 'date'),
     Input('trip-end-date', 'date'),
     Input('trip-schedule-items', 'data')],
    prevent_initial_call=False
)
def populate_timeline(start_date, end_date, schedule_items):
    """Create day drop zones based on selected date range"""
    from datetime import datetime, timedelta

    if not start_date or not end_date:
        return html.Div([
            html.Div([
                html.I(className='fas fa-calendar-alt', style={'fontSize': '3rem', 'color': '#ddd', 'marginBottom': '1rem'}),
                html.P("Select start and end dates above", style={'color': '#888', 'fontSize': '1.1rem'}),
                html.P("to see your trip timeline", style={'color': '#aaa', 'fontSize': '0.9rem'})
            ], style={'textAlign': 'center', 'padding': '4rem 2rem'})
        ])

    try:
        start = datetime.fromisoformat(start_date.split('T')[0])
        end = datetime.fromisoformat(end_date.split('T')[0])

        if end < start:
            return html.Div("End date must be after start date", style={'padding': '2rem', 'textAlign': 'center', 'color': '#dc3545'})

        num_days = (end - start).days + 1

        if num_days > 30:
            return html.Div("Trip is too long (max 30 days)", style={'padding': '2rem', 'textAlign': 'center', 'color': '#dc3545'})

        # Organize items by day
        items_by_day = {i: [] for i in range(1, num_days + 1)}
        if schedule_items:
            for day_key, items in schedule_items.items():
                day_num = int(day_key)
                if day_num in items_by_day:
                    items_by_day[day_num] = items

        # Create drop zones for each day
        day_zones = []
        for day in range(1, num_days + 1):
            day_zones.append(create_day_drop_zone(day, items_by_day[day]))

        return day_zones

    except Exception as e:
        return html.Div(f"Error: {str(e)}", style={'padding': '2rem', 'textAlign': 'center', 'color': '#dc3545'})


# ===== CALLBACK 4: Clientside Drag-and-Drop Handler =====
app.clientside_callback(
    """
    function(n_intervals) {
        // Set up drag event handlers
        document.addEventListener('DOMContentLoaded', function() {
            setupDragAndDrop();
        });

        // If DOM is already loaded
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(setupDragAndDrop, 100);
        }

        function setupDragAndDrop() {
            // Get all draggable items
            const draggables = document.querySelectorAll('.draggable-item');
            const dropZones = document.querySelectorAll('.drop-zone');

            draggables.forEach(draggable => {
                draggable.addEventListener('dragstart', handleDragStart);
                draggable.addEventListener('dragend', handleDragEnd);
            });

            dropZones.forEach(zone => {
                zone.addEventListener('dragover', handleDragOver);
                zone.addEventListener('dragleave', handleDragLeave);
                zone.addEventListener('drop', handleDrop);
            });
        }

        let draggedItem = null;

        function handleDragStart(e) {
            draggedItem = {
                type: e.target.dataset.itemType,
                id: e.target.dataset.itemId,
                name: e.target.dataset.itemName
            };
            e.target.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', e.target.innerHTML);
        }

        function handleDragEnd(e) {
            e.target.classList.remove('dragging');
        }

        function handleDragOver(e) {
            if (e.preventDefault) e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            e.currentTarget.classList.add('drag-over');
            return false;
        }

        function handleDragLeave(e) {
            e.currentTarget.classList.remove('drag-over');
        }

        function handleDrop(e) {
            if (e.stopPropagation) e.stopPropagation();
            e.preventDefault();

            e.currentTarget.classList.remove('drag-over');

            if (draggedItem) {
                const dayNum = e.currentTarget.dataset.day;

                // Get current schedule
                const scheduleStore = document.getElementById('trip-schedule-items');
                let schedule = {};
                try {
                    schedule = JSON.parse(scheduleStore.getAttribute('data-dash-is-loading')) || {};
                } catch {
                    schedule = {};
                }

                // Add item to this day
                if (!schedule[dayNum]) {
                    schedule[dayNum] = [];
                }

                // Check if item already exists
                const exists = schedule[dayNum].some(item =>
                    item.item_id === draggedItem.id && item.item_type === draggedItem.type
                );

                if (!exists) {
                    schedule[dayNum].push({
                        item_type: draggedItem.type,
                        item_id: draggedItem.id,
                        item_name: draggedItem.name
                    });

                    // Update store (trigger callback to refresh timeline)
                    const event = new CustomEvent('update-schedule', {
                        detail: { schedule: schedule }
                    });
                    document.dispatchEvent(event);
                }
            }

            return false;
        }

        return window.dash_clientside.no_update;
    }
    """,
    Output('trip-schedule-items', 'data', allow_duplicate=True),
    Input('url', 'pathname'),  # Trigger on page load
    prevent_initial_call=False
)


# ===== CALLBACK 5: Remove Item from Schedule =====
@app.callback(
    Output('trip-schedule-items', 'data', allow_duplicate=True),
    Input({'type': 'remove-from-schedule', 'day': ALL, 'item-id': ALL, 'item-type': ALL}, 'n_clicks'),
    State('trip-schedule-items', 'data'),
    prevent_initial_call=True
)
def remove_from_schedule(n_clicks, schedule_items):
    """Remove an item from the schedule"""
    from dash import callback_context

    if not any(n_clicks):
        raise PreventUpdate

    ctx = callback_context
    triggered_id = ctx.triggered_id
    if not triggered_id:
        raise PreventUpdate

    day = str(triggered_id['day'])
    item_id = triggered_id['item-id']
    item_type = triggered_id['item-type']

    if not schedule_items:
        schedule_items = {}

    # Remove the item
    if day in schedule_items:
        schedule_items[day] = [
            item for item in schedule_items[day]
            if not (item['item_id'] == item_id and item['item_type'] == item_type)
        ]
        # Remove day if empty
        if not schedule_items[day]:
            del schedule_items[day]

    return schedule_items
