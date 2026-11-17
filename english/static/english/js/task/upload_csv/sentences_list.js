const sentencesListTemplate = document.getElementById("sentencesListTemplate");
const sentenceRowTemplate = document.getElementById("sentenceRowTemplate");
const sentenceAnswerInput = document.getElementById("sentenceAnswerInput");
const sentencePromptInput = document.getElementById("sentencePromptInput");
const saveSentenceButton = document.getElementById("saveSentenceButton");

const confirmSentenceButton = document.getElementById("confirmSentenceButton");
const sentenceGapTokenTemplate = document.getElementById("sentenceGapTokenTemplate");
const backSentenceGapsButton = document.getElementById("backSentenceGapsButton");
const saveSentenceGapsButton = document.getElementById("saveSentenceGapsButton");

const SENTENCES_LIST_TITLE = "Список речень";
const sentencesByStepId = new Map();


document.addEventListener("uploadCsvImported", (event) => {
    renderSentencesList(event.detail.data);
});

saveSentenceButton.addEventListener('click', async (event) => {
    
    if (!isValidSentenceForm()) {
        return;
    }

    saveSentenceButton.disabled = true;

    try {
        const responseData = await sentenceRequest(
            getSentenceSaveUrl(), 
            {
                answer: sentenceAnswerInput.value.trim(),
                prompt: sentencePromptInput.value.trim()
            }
        );

        renderSentencesList(responseData.data);
        closeSentenceForm();
    } catch (error) {
        showMessage(error.message);
    } finally {
        saveSentenceButton.disabled = false;
    }
});

uploadCsvModal.addEventListener("click", (event) => {
    
    if (event.target.closest(".add-sentence-button")) {
        openSentenceForm("create");
        return;
    }


    const row = event.target.closest(".sentence-row");

    if (!row) {
        return;
    }

    const sentence = sentencesByStepId.get(
        Number(row.dataset.stepId)
    );

    if (sentence) {
        openSentenceForm("edit", sentence);
    }
});

confirmSentenceButton.addEventListener("click", async (event) => {
    
    if (!isValidSentenceForm) {
        return;
    }

    const answer = sentenceAnswerInput.value.trim();

    confirmSentenceButton.disabled = true;

    try {
        const responseData = await sentenceRequest(
            uploadCsvModal.dataset.previewSentenceUrl,
            {
                answer: answer,
                prompt: sentencePromptInput.value.trim()
            }
        )

        if (sentenceFormState.previewAnswer !== answer) {
            sentenceFormState.gaps = [];
        }

        sentenceFormState.previewAnswer = answer;

        renderSentenceGaps(responseData.data.tokens);
        openSentenceGaps();
    } catch (error) {
        showMessage(error.message);
    } finally {
        confirmSentenceButton.disabled = false;
    }
});

sentenceGapsPreview.addEventListener('click', (event) => {
    const token = event.target.closest(".sentence-gap-token");

    if (!token) {
        return;
    }

    toggleSentenceGap(token);
});

// Переключение на режим назад, к основному режиму модалки создания/редактирования
// где сами предложения еще вводтся
// без выбора пропусков
backSentenceGapsButton.addEventListener("click", () => {
    uploadCsvModal.classList.remove("is-sentence-gaps");
    uploadCsvModal.classList.add("is-sentence-form");
});

saveSentenceGapsButton.addEventListener("click", async () => {
    saveSentenceGapsButton.disabled = true;

    try {
        const responseData = await sentenceRequest(getSentenceSaveUrl(), {
            answer: sentenceAnswerInput.value.trim(),
            prompt: sentencePromptInput.value.trim(),
            gaps: sentenceFormState.gaps.slice().sort((a, b) => a - b)
        });

        renderSentencesList(responseData.data);
        closeSentenceForm();
    } catch (error) {
        showMessage(error.message);
        saveSentenceGapsButton.disabled = sentenceFormState.gaps.length === 0;
    }
});


function renderSentenceGaps(tokens) {
    sentenceGapsPreview.replaceChildren();

    for (const token of tokens) {
        // Пропускаем не слова или не цифры. Таким образом - пропускаем разделительные знаки в отображении
        // Ествественно, is_word записан сервером, здесь лишь пользуемся его данными
        if (!token.is_word) {
            continue;
        }

        const button = sentenceGapTokenTemplate.content.firstElementChild.cloneNode(true);

        button.textContent = token.text;
        button.dataset.index = token.index;
        button.classList.toggle('is-gap', sentenceFormState.gaps.includes(token.index));

        sentenceGapsPreview.append(button);
    }

    // Пока не выбраны пропуски, кнопка не будет активирована для юзера
    saveSentenceGapsButton.disabled = sentenceFormState.gaps.length === 0;

}

function openSentenceGaps() {
    uploadCsvModal.classList.remove('is-sentence-form');
    uploadCsvModal.classList.add('is-sentence-gaps');
}

function toggleSentenceGap(token) {

    const index = Number(token.dataset.index);
    const gaps = sentenceFormState.gaps;

    if (gaps.includes(index)) {
        gaps.splice(gaps.indexOf(index), 1);
    } else {
        gaps.push(index);
    }

    token.classList.toggle("is-gap", gaps.includes(index));
    saveSentenceGapsButton.disabled = gaps.length === 0;
}


function renderSentencesList(data) {
    sentencesByStepId.clear();
    // data.is_fill приходит с сервера, и говорит о том, является ли предложение варианта "Скласти" или же "Доповнити"
    uploadCsvModal.classList.toggle("is-fill-sentences", data.is_fill);

    const block = sentencesListTemplate.content.firstElementChild.cloneNode(true);
    const list = block.querySelector(".sentences-list");

    for (const sentence of data.sentences) {
        list.append(
            createSentenceRow(sentence, data.required_correct_answers)
        );
    }

    // uploadcsvList и uploadCsvTitle взято из elements.js
    uploadCsvList.replaceChildren(block);
    uploadCsvTitle.textContent = SENTENCES_LIST_TITLE;
}

function createSentenceRow(sentence, requiredCorrectAnswers) {
    const rowItem = sentenceRowTemplate.content.firstElementChild.cloneNode(true);
    const row = rowItem.querySelector(".sentence-row");
    const progress = rowItem.querySelector(".word-progress");

    row.dataset.stepId = sentence.step_id;
    row.querySelector(".sentence-text").textContent = sentence.answer;

    for (let index = 0; index < requiredCorrectAnswers; index++) {
        const dot = document.createElement("span");

        dot.className = "progress-dot";
        progress.append(dot);
    }

    sentencesByStepId.set(sentence.step_id, sentence);
    return rowItem;
}

cancelSentenceButton.addEventListener("click", () => {
    closeSentenceForm();
});

function resetSentenceForm() {
    
    sentenceFormState = {
        mode: null, 
        stepId: null,
        gaps: []
    };

    sentenceAnswerInput.value = "";
    sentencePromptInput.value = "";
    sentenceGapsPreview.replaceChildren();
}

function openSentenceForm(mode, sentence) {
    resetSentenceForm();

    sentenceFormState.mode = mode;

    if (mode === "edit") {
        sentenceFormState.stepId = sentence.step_id;
        sentenceAnswerInput.value = sentence.answer;
        sentencePromptInput.value = sentence.prompt;
        sentenceFormState.previewAnswer = sentence.answer;

        if (sentence.gaps) {
            // копируем выбранные пропуски прямиков в состояние
            sentenceFormState.gaps = sentence.gaps.slice();
        }
    }

    uploadCsvModal.classList.remove("is-sentence-gaps");
    uploadCsvModal.classList.add("is-sentence-form");
    uploadCsvTitle.textContent = mode === "create" ? CREATE_SENTENCE_TITLE : EDIT_SENTENCE_TITLE;
}
function closeSentenceForm() {
    uploadCsvModal.classList.remove("is-sentence-form", "is-sentence-gaps");
    uploadCsvTitle.textContent = SENTENCES_LIST_TITLE;
    resetSentenceForm();
}

function isValidSentenceForm() {
    if (!sentenceAnswerInput.value.trim()) {
        showMessage("Введіть речення англійською");
        return false;
    }

    if (!sentencePromptInput.value.trim()) {
        showMessage("Введіть речення українською");
        return false;
    }

    return true;
}

function getSentenceSaveUrl() {
    if (sentenceFormState.mode === "create") {
        return uploadCsvModal.dataset.createSentenceUrl;
    }

    // "/\/0\/$/" - без выделения просто "/0/"
    // берем именно такой кусок маршрута, потому что просто "0" 
    // может быть использовать уже в других частях машрута
    return uploadCsvModal.dataset.updateSentenceUrl.replace(/\/0\/$/, `/${sentenceFormState.stepId}/`);
}

async function sentenceRequest(url, data) {
    
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        },
        body: JSON.stringify(data)
    });

    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(responseData.error || "Не вдалося зберегти речення");
    }

    return responseData;
}