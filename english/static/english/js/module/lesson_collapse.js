const collapseButtons = document.querySelectorAll(".collapse-button");

collapseButtons.forEach((button) => {
    const lessonCard = button.closest(".lesson-card");

    if (!lessonCard) {
        return;
    }

    const header = lessonCard.querySelector(".card-header");

    const toggleLesson = () => {
        lessonCard.classList.toggle("collapsed");
    };

    button.addEventListener("click", toggleLesson);

    if (header) {
        header.addEventListener("click", toggleLesson);
    }
});