function resetLessonEdits(lessonCard) {
    lessonCard.querySelectorAll(".task-name-input").forEach((input) => {
        input.value = input.defaultValue;
    });

    lessonCard.querySelectorAll(".task-card.is-deleted").forEach((card) => {
        card.classList.remove("is-deleted");
    });
}

const changeLessonButtons = document.querySelectorAll(".change-lesson-button");

changeLessonButtons.forEach((button) => {
    button.addEventListener("click", () => {
        
        // Урок который редактируется сейчас
        const lessonCard = button.closest(".lesson-card");

        // Урок, кототрый редактровался до этого момента
        const editedLessonCard = document.querySelector(".lesson-card.is-editing");
        

        // Урок, который редактировался до этого, 
        // выходит из режима редактирования без сохранения изменений
        if (editedLessonCard && editedLessonCard != lessonCard) {
            resetLessonEdits(editedLessonCard);

            editedLessonCard.classList.remove("is-editing");
        }
        
        lessonCard.classList.toggle("is-editing");
    });
});
