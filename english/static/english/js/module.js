
const collapseButtons = document.querySelectorAll(".collapse-button");

collapseButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const lessonCard = button.closest(".lesson-card");
        const isCollapsed = lessonCard.classList.toggle("collapsed");

        

    });
})

