const taskDeleteButtons = document.querySelectorAll(".task-delete-button");

taskDeleteButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const taskCard = button.closest(".task-card");

        taskCard.classList.add("is-deleted");
    });
});
