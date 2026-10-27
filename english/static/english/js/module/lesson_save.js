
const saveLessonButtons = document.querySelectorAll(".save-lesson-button");

// отдельный флаг, от значения которого зависит 
// отправка запроса на редактирование данных сервером
let hasErrors = false;

saveLessonButtons.forEach((button) => {
    button.addEventListener("click", async () => {
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
        
        // Переводим фокус на первое из полей, в которых возникла ошибка
        if (hasErrors) {
            lessonCard.querySelector(".validation-error .task-name-input").focus();
            return;
        }

        console.log(editedData)

        // Если данные урока (задания) не были изменены
        // То по нажатию кнопки "Зберегти" запрос отправлен НЕ БУДЕТ
        // Очевидно, потому что это бессмысленно
        if (
            editedData.renamed.length === 0 && 
            editedData.deleted.length === 0) {
                setLessonEditing(lessonCard, false);
                return;
        }
        
        // Снимаем режим редактирования и отправляем запрос на редактироваие
        // только после успешного прохождения всех проверок
        try {
            await lessonSaveRequest(editedData);
            lessonCard.classList.toggle("is-editing");

            applySavedEdits(lessonCard);
            setLessonEditing(lessonCard, false);

        } catch (error) {
            console.error(error);
        }
    });
});

function applySavedEdits(lessonCard) {
    // Видалені на сервері — прибираємо з DOM
    lessonCard.querySelectorAll(".task-card.is-deleted").forEach((card) => {
        card.remove();
    });

    // Збережені назви стають «вихідними»
    lessonCard.querySelectorAll(".task-card").forEach((card) => {
        const input = card.querySelector(".task-name-input");
        const name = input.value.trim();

        input.value = name;
        input.defaultValue = name;
        card.querySelector(".task-pill-name").textContent = name;
    });
}