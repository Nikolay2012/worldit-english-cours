const sentencesListTemplate = document.getElementById("sentencesListTemplate");
const sentenceRowTemplate = document.getElementById("sentenceRowTemplate");
const sentenceAnswerInput = document.getElementById("sentenceAnswerInput");
const sentencePromptInput = document.getElementById("sentencePromptInput");

const SENTENCES_LIST_TITLE = "Список речень";
const sentencesByStepId = new Map();

document.addEventListener("uploadCsvImported", (event) => {
    renderSentencesList(event.detail.data);
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
        sentenceFormState.stepId = sentence.stepId;
        sentenceFormState.answerValue = sentence.answer;
        sentenceFormState.promptValue = sentence.prompt;

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