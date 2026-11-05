const wordsPanel = document.getElementById("wordsPanel");
const wordsPanelCover = document.getElementById("wordsPanelCover");
const openWordsPanelButton = document.getElementById("openWordsPanelButton");
const closeWordsPanelButton = document.getElementById("closeWordsPanelButton");
const wordsPanelBody = document.getElementById("wordsPanelBody");
const wordsPanelCategoryTemplate = document.getElementById("wordsPanelCategoryTemplate");
const wordsPanelRowTemplate = document.getElementById("wordsPanelRowTemplate");
const deleteWordsPanelListButton = document.getElementById("deleteWordsPanelListButton");
const saveWordsPanelButton = document.getElementById("saveWordsPanelButton");


const canEditWords = wordsPanel?.dataset.canEdit === "true";

const wordsPanelWordsByStepId = new Map();


if (wordsPanel && openWordsPanelButton) {
    openWordsPanelButton.addEventListener("click", () => {
        setWordsPanelOpen(true);
        loadWordsProgress();
    });

    closeWordsPanelButton.addEventListener("click", () => {
        setWordsPanelOpen(false);
    });

    wordsPanelCover.addEventListener("click", () => {
        setWordsPanelOpen(false);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape" || !wordsPanel.classList.contains("is-open")) {
            return;
        }

        if (canEditWords && isOpenedFromWordsPanel) {
            return;
        }

        setWordsPanelOpen(false);
    });

    if (canEditWords) {
        wordsPanelBody.addEventListener("click", (event) => {
            const addButton = event.target.closest(".words-panel-add-button");

            if (addButton) {
                openUploadCsvFromWordsPanel(
                    "create", 
                    {
                        category: addButton.dataset.category
                    }
                );
                return;
            }

            const row = event.target.closest(".words-panel-row.is-editable");

            if (row) {
                openUploadCsvFromWordsPanel(
                    "edit",
                    wordsPanelWordsByStepId.get(Number(row.dataset.stepId))
                );
            }
        });

        deleteWordsPanelListButton.addEventListener("click", () => {
            openUploadCsvFromWordsPanel("delete");
        });

        saveWordsPanelButton.addEventListener("click", () => {
            window.location.reload();
        });

        document.addEventListener("wordsPanelReturn", () => {
            loadWordsProgress();
        });
    }
}

function setWordsPanelOpen(isOpen) {
    wordsPanel.classList.toggle("is-open", isOpen);
    wordsPanelCover.classList.toggle("is-open", isOpen);
    document.body.classList.toggle("is-words-panel-open", isOpen);
}

async function loadWordsProgress() {
    try {
        const data = await wordsProgressRequest(
            wordsPanel.dataset.wordsProgressUrl
        );
        renderWordsProgress(data);
    } catch (error) {
        showMessage(error.message)
    }
}

function renderWordsProgress(data) {
    wordsPanelBody.replaceChildren();
    wordsPanelWordsByStepId.clear();

    for (const category of data.categories) {
        const section = wordsPanelCategoryTemplate.content.firstElementChild.cloneNode(true);
        const list = section.querySelector(".words-panel-list");
        const addButton = section.querySelector(".words-panel-add-button")

        section.querySelector(".words-panel-category-title").textContent = category.category

        if (canEditWords) {
            addButton.dataset.category = category.category;
        } else {
            addButton.remove();
        }

        for (const word of category.words) {
            list.append(
                createWordsPanelRow(word, data.required_correct_answers)
            );
        }

        wordsPanelBody.append(section);
    }
}

function createWordsPanelRow(word, requiredCorrectAnswers) {
    const row = wordsPanelRowTemplate.content.firstElementChild.cloneNode(true);
    const progress = row.querySelector(".words-panel-progress");

    row.querySelector(".words-panel-word").textContent = word.text;
    row.querySelector(".words-panel-translation").textContent = word.translation;

    for (let index = 0; index < requiredCorrectAnswers; index++) {
        const dot = document.createElement("span");

        dot.className = "words-panel-dot";
        // Отмечаем точку, как заполненную, 
        // если её индекс меньше количества правильных ответов
        // Так это потому, что правильные ответы всегда расположены слева
        dot.classList.toggle("is-filled", index < word.correct_count);

        progress.append(dot);
    }

    if (canEditWords) {
        row.classList.add("is-editable");
        row.dataset.stepId = word.step_id;

        wordsPanelWordsByStepId.set(word.step_id, {
            step_id: word.step_id,
            question: {
                text: word.text
            },
            translation: word.translation,
            images: word.images
        });
    }

    return row;
}

async function wordsProgressRequest(url) {
    const response = await fetch(url);
    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(responseData.error || "Не вдалося отримати список слів");
    }

    return responseData.data;
}
