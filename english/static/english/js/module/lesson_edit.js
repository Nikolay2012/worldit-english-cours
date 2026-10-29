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
        
        if (editedLessonCard) {
            setLessonEditing(editedLessonCard, false);
        }

        setLessonEditing(lessonCard, true);
    });
});

function setLessonEditing(lessonCard, isEditing) {
    lessonCard.classList.toggle("is-editing", isEditing);

    if (isEditing) {
        lessonCard.classList.remove("collapsed");
    }

    const createTaskButton = lessonCard.querySelector(".create-english-task-button");
    
    if (createTaskButton) {
        createTaskButton.disabled = isEditing;
    }
}
