const collapseButtons = document.querySelectorAll(".collapse-button");

const OPENED_LESSONS_KEY = "openedLessons";

collapseButtons.forEach((button) => {
    const lessonCard = button.closest(".lesson-card");

    if (!lessonCard) {
        return;
    }

    const header = lessonCard.querySelector(".card-header");

    const toggleLesson = () => {
        lessonCard.classList.toggle("collapsed");
        saveLessonState(lessonCard);
    };

    button.addEventListener("click", toggleLesson);

    if (header) {
        header.addEventListener("click", toggleLesson);
    }
});

restoreOpenedLessons();

function getOpenedLessonIds() {
    try {
        return new Set(JSON.parse(localStorage.getItem(OPENED_LESSONS_KEY)) || []);
    } catch {
        return new Set();
    }
}

function saveLessonState(card) {
    const openedLessonIds = getOpenedLessonIds();

    if (card.classList.contains("collapsed")) {
        openedLessonIds.delete(card.dataset.id);
    } else {
        openedLessonIds.add(card.dataset.id);
    }

    try {
        localStorage.setItem(OPENED_LESSONS_KEY, JSON.stringify([...openedLessonIds]));
    } catch {
        return;
    }
}

function restoreOpenedLessons() {
    const openedLessonIds = getOpenedLessonIds();

    document.querySelectorAll(".lesson-card[data-id]").forEach((card) => {
        
        if (openedLessonIds.has(card.dataset.id)) {
            card.classList.remove("collapsed");
        }
    });
}