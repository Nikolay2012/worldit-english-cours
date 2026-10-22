// Before modal part
const taskDeleteButtons = document.querySelectorAll(".task-delete-button");

// Modal part
const deleteTaskModal = document.getElementById("deleteTaskModal");
const cancelDeleteTaskButton = document.getElementById("cancelDeleteTaskButton");
const confirmDeleteTaskButton = document.getElementById("confirmDeleteTaskButton");

cancelDeleteTaskButton.addEventListener("click", closeModal);

taskDeleteButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const taskCard = button.closest(".task-card");

        openModal(deleteTaskModal);

        confirmDeleteTaskButton.addEventListener("click", () => {
            taskCard.classList.add("is-deleted");
            closeModal();
        });
    });
});
