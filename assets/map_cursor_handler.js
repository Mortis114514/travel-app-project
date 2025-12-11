/**
 * Scatter Map Cursor Handler
 * Changes cursor to pointer when hovering over clickable points on the map
 */

// Function to handle cursor changes for scatter map points
function setupMapCursorHandler(graphId) {
    const graphDiv = document.getElementById(graphId);

    if (!graphDiv) {
        console.warn(`Graph element with id '${graphId}' not found`);
        return;
    }

    // Listen for hover events on the graph
    graphDiv.on('plotly_hover', function(data) {
        // When hovering over a point, change cursor to pointer
        const mapCanvas = graphDiv.querySelector('.mapboxgl-canvas-container');
        if (mapCanvas) {
            mapCanvas.style.cursor = 'pointer';
        }
    });

    // Listen for unhover events
    graphDiv.on('plotly_unhover', function(data) {
        // When not hovering over a point, change cursor back to grab
        const mapCanvas = graphDiv.querySelector('.mapboxgl-canvas-container');
        if (mapCanvas) {
            mapCanvas.style.cursor = 'grab';
        }
    });

    // Handle dragging state
    let isDragging = false;

    if (graphDiv) {
        graphDiv.addEventListener('mousedown', function() {
            isDragging = true;
            const mapCanvas = graphDiv.querySelector('.mapboxgl-canvas-container');
            if (mapCanvas) {
                mapCanvas.style.cursor = 'grabbing';
            }
        });

        graphDiv.addEventListener('mouseup', function() {
            isDragging = false;
            const mapCanvas = graphDiv.querySelector('.mapboxgl-canvas-container');
            if (mapCanvas) {
                mapCanvas.style.cursor = 'grab';
            }
        });
    }
}

// Initialize cursor handlers when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            setupMapCursorHandler('restaurant-map-graph');
            setupMapCursorHandler('hotel-map-graph');
        }, 1000);  // Wait for Plotly to render
    });
} else {
    // DOM already loaded
    setTimeout(function() {
        setupMapCursorHandler('restaurant-map-graph');
        setupMapCursorHandler('hotel-map-graph');
    }, 1000);
}

// Also set up handlers when view mode changes
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length) {
            mutation.addedNodes.forEach(function(node) {
                if (node.id === 'restaurant-map-graph' || node.id === 'hotel-map-graph') {
                    setTimeout(function() {
                        setupMapCursorHandler(node.id);
                    }, 500);
                }
            });
        }
    });
});

// Observe the main content area for changes
setTimeout(function() {
    const mainContent = document.querySelector('body');
    if (mainContent) {
        observer.observe(mainContent, {
            childList: true,
            subtree: true
        });
    }
}, 500);
