const saveLessonButtons = document.querySelectorAll(".save-lesson-button");

saveLessonButtons.forEach((button) => {
    button.addEventListener("click", () => {
        // Контейнер текущего урока, задания которого редактируются
        const lessonCard = button.closest(".lesson-card");

        // Сбор отредактированных данных для отправки на сервер
        let editedData = {
            lessonId: null,
            renamed: [],
            deleted: []
        };

        const lessonId = button.getAttribute('lesson-id');
        editedData.lessonId = lessonId;

        lessonCard.querySelectorAll(".task-card").forEach((card) => {
            const taskId = card.dataset.taskId;

            if (card.classList.contains("is-deleted")) {
                editedData.deleted.push(taskId);
                // удаленное задание не должно попасть в массив renamed
                return;
            }

            const taskNameInput = card.querySelector('.task-name-input');
            const name = taskNameInput.value.trim();

            if (name != taskNameInput.defaultValue) {
                const taskPillName = card.querySelector(".task-pill-name");
                taskPillName.textContent = name;

                editedData.renamed.push({
                    taskId: taskId,
                    name: name
                });
            }
        });
        
        console.log(editedData);

        // Снимаем режим редактирования только после
        lessonCard.classList.toggle("is-editing");
    });
});
