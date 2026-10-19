
const saveLessonButtons = document.querySelectorAll(".save-lesson-button");

// отдельный флаг, от значения которого зависит 
// отправка запроса на редактирование данных сервером
let hasErrors = false;

saveLessonButtons.forEach((button) => {
    button.addEventListener("click", () => {
        hasErrors = false;

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
            const isEmptyName = name === "";

            // проверка на пустотоу полей
            card.querySelector(".task-pill").classList.toggle(
                "validation-error", 
                isEmptyName
            );

            console.log(isEmptyName);

            if (isEmptyName) {
                hasErrors = true;
                return;
            }

            if (name != taskNameInput.defaultValue) {

                const taskPillName = card.querySelector(".task-pill-name");
                taskPillName.textContent = name;

                editedData.renamed.push({
                    taskId: taskId,
                    name: name
                });
            }
        });
        
        // переводим фокус на первое из полей, в которых возникла ошибка
        if (hasErrors) {
            lessonCard.querySelector(".validation-error .task-name-input").focus();
            return;
        }
        
        // Снимаем режим редактирования и отправляем запрос на редактироваие
        // только после успешного прохождения всех проверок
        // -отправка запроса-
        lessonCard.classList.toggle("is-editing");
    });
});
