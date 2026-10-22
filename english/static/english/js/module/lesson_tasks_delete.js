// Кнопка из контейнера самого задания
const taskDeleteButtons = document.querySelectorAll(".task-delete-button");

// Модальное окно подтверждения удаления задания и кнопки модалки
const deleteTaskModal = document.getElementById("deleteTaskModal");
const cancelDeleteTaskButton = document.getElementById("cancelDeleteTaskButton");
const confirmDeleteTaskButton = document.getElementById("confirmDeleteTaskButton");

let taskCardToDelete = null;

taskDeleteButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const taskCard = button.closest(".task-card");

        taskCardToDelete = taskCard;
        
        // Указываем название
        const taskName = taskCard.querySelector(".task-pill-name");
        const deleteTaskNameSpan = document.getElementById("deleteTaskName");
        deleteTaskNameSpan.textContent = taskName.textContent

        openModal(deleteTaskModal);
    });
});

// Кнопка "Скасувати"
cancelDeleteTaskButton.addEventListener("click", () => {
    taskCardToDelete = null;
    closeModal();
});

// Кнопка "Видалити"
confirmDeleteTaskButton.addEventListener("click", () => {
    
    if (!taskCardToDelete) {
        return;
    }

    taskCardToDelete.classList.add("is-deleted");
    taskCardToDelete = null;

    closeModal();
});
