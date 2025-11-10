// Close dropdown menus when clicking outside
document.addEventListener('DOMContentLoaded', function() {
    // Wait for elements to be available
    setTimeout(function() {
        document.addEventListener('click', function(event) {
            const cuisineMenu = document.getElementById('cuisine-dropdown-menu');
            const ratingMenu = document.getElementById('rating-dropdown-menu');
            const cuisineTrigger = document.getElementById('cuisine-trigger');
            const ratingTrigger = document.getElementById('rating-trigger');
            const cuisineIcon = document.getElementById('cuisine-icon');
            const ratingIcon = document.getElementById('rating-icon');

            if (!cuisineMenu || !ratingMenu) return;

            // Check if click is outside both dropdowns and triggers
            const clickedOutside =
                !cuisineMenu.contains(event.target) &&
                !ratingMenu.contains(event.target) &&
                !cuisineTrigger.contains(event.target) &&
                !ratingTrigger.contains(event.target) &&
                event.target !== cuisineIcon &&
                event.target !== ratingIcon;

            if (clickedOutside) {
                // Close both menus
                if (cuisineMenu.style.display === 'block') {
                    cuisineMenu.style.display = 'none';
                }
                if (ratingMenu.style.display === 'block') {
                    ratingMenu.style.display = 'none';
                }
            }
        });
    }, 500);
});
