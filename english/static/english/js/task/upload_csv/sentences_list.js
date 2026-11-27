const sentencesListTemplate = document.getElementById("sentencesListTemplate");
const sentenceRowTemplate = document.getElementById("sentenceRowTemplate");
const sentenceAnswerInput = document.getElementById("sentenceAnswerInput");
const sentencePromptInput = document.getElementById("sentencePromptInput");
const saveSentenceButton = document.getElementById("saveSentenceButton");

const confirmSentenceButton = document.getElementById("confirmSentenceButton");

const SENTENCES_LIST_TITLE = "Список речень";
const sentencesByStepId = new Map();


document.addEventListener("uploadCsvImported", (event) => {
    renderSentencesList(event.detail.data);
});

saveSentenceButton.addEventListener('click', async (event) => {
    
    if (!isValidSentenceForm()) {
        return;
    }

    if (isOpenedFromSentencesPanel) {
        returnToSentencesPanel(collectSentenceChange());
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
    
    if (!isValidSentenceForm()) {
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
            sentenceFormState.inserts = [];
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

function openSentenceGaps() {
    uploadCsvModal.classList.remove('is-sentence-form');
    uploadCsvModal.classList.add('is-sentence-gaps');
}

function renderSentencesList(data) {
    sentencesByStepId.clear();
    // data.is_fill приходит с сервера, и говорит о том, является ли предложение варианта "Скласти" или же "Доповнити"
    uploadCsvModal.classList.toggle("is-fill-sentences", data.is_fill);

    const block = sentencesListTemplate.content.firstElementChild.cloneNode(true);
    const list = block.querySelector(".sentences-list");

    for (const sentence of data.sentences) {
        list.append(
            createSentenceRow(sentence)
        );
    }

    // uploadcsvList и uploadCsvTitle взято из elements.js
    uploadCsvList.replaceChildren(block);
    uploadCsvTitle.textContent = SENTENCES_LIST_TITLE;
}

function createSentenceRow(sentence) {
    const rowItem = sentenceRowTemplate.content.firstElementChild.cloneNode(true);
    const row = rowItem.querySelector(".sentence-row");

    row.dataset.stepId = sentence.step_id;
    renderSentenceText(
        row.querySelector(".sentence-text"), 
        sentence.parts
    );
    row.title = sentence.answer;

    sentencesByStepId.set(sentence.step_id, sentence);
    return rowItem;
}

cancelSentenceButton.addEventListener("click", () => {

    if (isOpenedFromSentencesPanel) {
        returnToSentencesPanel();
        return;
    }

    closeSentenceForm();
});

function resetSentenceForm() {
    
    sentenceFormState = {
        mode: null, 
        stepId: null,
        gaps: [],
        previewAnswer: null,
        inserts: []
    };

    sentenceAnswerInput.value = "";
    sentencePromptInput.value = "";
    sentenceGapsPreview.replaceChildren();
    clearPlacingToken();
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

        if (sentence.zero_gaps) {
            sentenceFormState.inserts = sentence.zero_gaps.map((position) => ({
                position: position,
                kind: "zero",
                text: "-"
            }));
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

function renderSentenceText(element, parts) {

    for (const part of parts) {
        if (part.kind == "text") {
            element.append(part.text);
            continue;
        }

        const span = document.createElement("span");
        span.className = part.kind === "gap" ? "sentence-text-gap" : "sentence-text-zero";
        span.textContent = part.kind === "gap" ? part.text : "___";

        element.append(span);
    }
}

function openUploadCsvFromSentencesPanel(mode, options = {}) {
    resetUploadCsvModal();
    isOpenedFromSentencesPanel = true;

    uploadCsvModal.classList.remove(
        "is-sentence-form", 
        "is-sentence-gaps"
    );
    
    setUploadCsvList(true);

    if (mode === "delete") {
        setUploadCsvConfirmDelete(true);
        openModal(uploadCsvModal);
        return;
    }

    uploadCsvModal.classList.toggle(
        "is-fill-sentences", 
        Boolean(options.isFill)
    );
    openSentenceForm(mode, options.sentence);

    if (options.change) {
        restoreSentenceChange(options.change);
    }

    openModal(uploadCsvModal);
}

function returnToSentencesPanel(change = null) {
    isOpenedFromSentencesPanel = false;
    closeSentenceForm();
    closeModal();

    document.dispatchEvent(new CustomEvent("sentencesPanelReturn", {
        detail: {
            change: change
        }
    }));
}

function collectSentenceChange() {
    const data = {
        answer: sentenceAnswerInput.value.trim(),
        prompt: sentencePromptInput.value.trim()
    };

    let parts = null;

    if (uploadCsvModal.classList.contains("is-fill-sentences")) {
        data.gaps = sentenceFormState.gaps.slice().sort((a, b) => a - b);
        data.inserts = sentenceFormState.inserts.map((insert) => ({...insert}));
        parts = buildSentenceChangeParts();
    }

    return {
        mode: sentenceFormState.mode,
        stepId: sentenceFormState.stepId,
        data: data,
        parts: parts
    };
}

function restoreSentenceChange(change) {
    sentenceAnswerInput.value = change.data.answer;
    sentencePromptInput.value = change.data.prompt;
    sentenceFormState.previewAnswer = change.data.answer;
    sentenceFormState.gaps = change.data.gaps ? change.data.gaps.slice() : [];
    sentenceFormState.inserts = change.data.inserts
        ? change.data.inserts.map((insert) => ({...insert}))
        : [];
}

// Шаблолн текста, определяющий то, 
// входит ли первый символ части предложения (part в массиве parts)
// в набор знаков (, . ! ? : ;)
// Необходимо для выделения тех случаев, когда попадаются именно знаки,
// ведь перед знаками не нужен пробел, они «прилепают» в прошлой части
const SENTENCE_NO_SPACE_BEFORE = /^[,.!?:;)]/;

function buildSentenceChangeParts() {
    const parts = [];

    for (let position = 0; position <= sentenceGapsTokens.length; position++) {
        for (const insert of sentenceFormState.inserts) {
            
            if (insert.position !== position) {
                continue;
            }

            parts.push(
                insert.kind === "zero"
                    ? {kind: "zero"}
                    : {kind: "text", text: insert.text}
            );
        }

        if (position === sentenceGapsTokens.length) {
            break;
        }

        const token = sentenceGapsTokens[position];

        parts.push({
            kind: sentenceFormState.gaps.includes(token.index) ? "gap" : "text",
            text: token.text
        });
    }

    return addSentencePartsSpaces(parts);
}

function addSentencePartsSpaces(parts) {
    const result = [];

    parts.forEach((part, index) => {
        // Проверка на то, прилипает ли часть предложения к предыдущей часть
        // Прилепает к предыдущей части только знак (, . ; : - ! ?)
        const isGlued = part.kind !== "zero" 
        && SENTENCE_NO_SPACE_BEFORE.test(part.text);

        // Если часть не первая, и не прилепает ли она к предыдущей
        if (index > 0 && !isGlued) {
            // Тогда добавляем пробел перед следующей частью
            result.push({
                kind: "text", 
                text: " "
            });
        }

        result.push(part);
    });

    return result;
}