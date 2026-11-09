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

const wordsPanelWordsByKey = new Map();

const pendingWordChanges = new Map();

let wordsPanelData = null;
let editingWordKey = null;
let newWordCounter = 0;


if (wordsPanel && openWordsPanelButton) {
    openWordsPanelButton.addEventListener("click", () => {
        setWordsPanelOpen(true);

        if (pendingWordChanges.size === 0) {
            loadWordsProgress();
        }
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
                newWordCounter += 1;
                editingWordKey = `new-${newWordCounter}`;

                openUploadCsvFromWordsPanel("create", { category: addButton.dataset.category });
                return;
            }

            const row = event.target.closest(".words-panel-row.is-editable");

            if (row) {
                editingWordKey = row.dataset.wordKey;

                const mode = editingWordKey.startsWith("new-") ? "create" : "edit";
                openUploadCsvFromWordsPanel(mode, wordsPanelWordsByKey.get(editingWordKey));
            }
        });

        deleteWordsPanelListButton.addEventListener("click", () => {
            openUploadCsvFromWordsPanel("delete");
        });

        saveWordsPanelButton.addEventListener("click", async () => {
            if (pendingWordChanges.size === 0) {
                window.location.reload();
                return;
            }

            saveWordsPanelButton.disabled = true;

            try {
                await wordsBatchRequest(wordsPanel.dataset.wordsBatchUrl, buildWordsBatchFormData());
                window.location.reload();
            } catch (error) {
                showMessage(error.message);
                saveWordsPanelButton.disabled = false;
            }
        });

        document.addEventListener("wordsPanelReturn", (event) => {
            const change = event.detail?.change;

            if (change && editingWordKey) {
                pendingWordChanges.set(editingWordKey, change);
                renderWordsProgress();
            }

            editingWordKey = null;
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
        wordsPanelData = await wordsProgressRequest(
            wordsPanel.dataset.wordsProgressUrl
        );

        renderWordsProgress();
    } catch (error) {
        console.error(error);
        showMessage(error.message);
    }
}

function renderWordsProgress() {
    wordsPanelBody.replaceChildren();
    wordsPanelWordsByKey.clear();

    for (const category of wordsPanelData.categories) {
        const section = wordsPanelCategoryTemplate.content.firstElementChild.cloneNode(true);
        const list = section.querySelector(".words-panel-list");
        const addButton = section.querySelector(".words-panel-add-button");

        section.querySelector(".words-panel-category-title").textContent = category.category;

        if (addButton) {
            addButton.dataset.category = category.category;
        }

        for (const word of category.words) {
            const change = pendingWordChanges.get(String(word.step_id));

            list.append(createWordsPanelRow(
                String(word.step_id),
                {
                    ...word,
                    text: change ? change.word : word.text,
                    translation: change ? change.translation : word.translation
                },
                change,
                wordsPanelData.required_correct_answers
            ));
        }

        for (const [key, change] of pendingWordChanges) {
            if (change.mode !== "create" || change.category !== category.category) {
                continue;
            }

            list.append(createWordsPanelRow(
                key,
                {
                    text: change.word,
                    translation: change.translation,
                    correct_count: 0,
                    images: []
                },
                change,
                wordsPanelData.required_correct_answers
            ));
        }

        wordsPanelBody.append(section);
    }
}

function createWordsPanelRow(key, word, change, requiredCorrectAnswers) {
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
        row.classList.toggle("is-changed", Boolean(change));
        row.dataset.wordKey = key;

        wordsPanelWordsByKey.set(key, {
            step_id: word.step_id,
            category: change ? change.category : null,
            question: { text: word.text },
            translation: word.translation,
            images: word.images,
            pendingImageStates: change ? change.imageStates : null
        });
    }

    return row;
}

function buildWordsBatchFormData() {
    const formData = new FormData();
    const changes = [];

    for (const [key, change] of pendingWordChanges) {
        const removedImages = [];

        change.imageStates.forEach((state, order) => {
            if (state.action === "replace") {
                formData.append(`image_${key}_${order}`, state.file);
            }

            if (state.action === "remove") {
                removedImages.push(order);
            }
        });

        changes.push({
            key: key,
            mode: change.mode,
            step_id: change.stepId,
            category: change.category,
            word: change.word,
            translation: change.translation,
            removed_images: removedImages
        });
    }

    formData.append("changes", JSON.stringify(changes));

    return formData;
}

async function wordsProgressRequest(url) {
    const response = await fetch(url);
    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(responseData.error || "Не вдалося отримати список слів");
    }

    return responseData.data;
}

async function wordsBatchRequest(url, formData) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        },
        body: formData
    });

    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(responseData.error || "Не вдалося зберегти зміни");
    }

    return responseData;
}