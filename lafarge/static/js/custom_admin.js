document.addEventListener("DOMContentLoaded", function() {
    $(document).on("shown.bs.modal", ".modal", function () {
        $(this).modal({
            backdrop: "static",  // Prevents closing when clicking outside
            keyboard: false      // Prevents closing with ESC key
        });
    });
});
