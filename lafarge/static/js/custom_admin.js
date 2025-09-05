$(document).ready(function() {
    console.log('Applying modal backdrop fix...');
    
    // More balanced approach - prevent backdrop clicks but allow ESC and close buttons
    $(document).on('show.bs.modal', '.modal', function() {
        var $modal = $(this);
        
        // Set backdrop to static (prevents closing on outside click)
        // But allow keyboard (ESC) to work
        if ($modal.data('bs.modal')) {
            $modal.data('bs.modal')._config.backdrop = 'static';
            $modal.data('bs.modal')._config.keyboard = true; // Allow ESC
        }
        
        console.log('Applied static backdrop to modal, ESC and buttons still work');
    });
    
    // Alternative: Just prevent backdrop clicks specifically
    $(document).on('click', '.modal', function(e) {
        // If click is on the modal backdrop (not the dialog), prevent default
        if (e.target === this) {
            e.stopPropagation();
            return false;
        }
    });
});