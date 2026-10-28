document.addEventListener("DOMContentLoaded", () => {
    // Ask for confirmation before cancelling a booking.
    document.querySelectorAll(".cancel-form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.dataset.confirm || "Are you sure you want to cancel this booking?";
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // Fade flash messages away after a few seconds.
    document.querySelectorAll(".flash").forEach((message) => {
        window.setTimeout(() => {
            message.classList.add("flash-hide");
            window.setTimeout(() => message.remove(), 450);
        }, 4500);
    });
});
