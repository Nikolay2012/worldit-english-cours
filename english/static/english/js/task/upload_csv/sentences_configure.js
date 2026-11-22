const sentenceGapTokenTemplate = document.getElementById("sentenceGapTokenTemplate");
const sentenceZeroGapTemplate = document.getElementById("sentenceZeroGapTemplate");
const sentenceInsertedMarkTemplate = document.getElementById("sentenceInsertedMarkTemplate");
const sentenceInsertSlotTemplate = document.getElementById("sentenceInsertSlotTemplate");
const sentenceGapsPalette = document.getElementById("sentenceGapsPalette");
const backSentenceGapsButton = document.getElementById("backSentenceGapsButton");
const saveSentenceGapsButton = document.getElementById("saveSentenceGapsButton");

let sentenceGapsTokens = [];
let placingToken = null;


sentenceGapsPalette.addEventListener("dragstart", (event) => {
    const token = event.target.closest(".sentence-token");

    if (!token) {
        return;
    }

    // токен, при перетаскивании, копируется и в палитре остается
    // так это потому, что юзер может добавить несколько запятых или точек, 
    // или прочих символов
    // Это не сборка предложения из ограниченного набора токенов
    event.dataTransfer.effectAllowed = "copy";
    setPlacingToken(token);
});

sentenceGapsPalette.addEventListener("dragend", () => {
    clearPlacingToken();
});

sentenceGapsPalette.addEventListener("click", (event) => {
    const token = event.target.closest(".sentence-token");

    if (!token) {
        return;
    }

    if (token.classList.contains("is-selected")) {
        clearPlacingToken();
        return;
    }

    setPlacingToken(token);
    token.classList.add("is-selected");
});

sentenceGapsPreview.addEventListener("dragover", (event) => {
    const slot = event.target.closest(".sentence-insert-slot");

    if (!slot || !placingToken) {
        return;
    }

    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
});

sentenceGapsPreview.addEventListener("drop", (event) => {
    const slot = event.target.closest(".sentence-insert-slot");

    if (!slot || !placingToken) {
        return;
    }

    event.preventDefault();
    insertPlacingToken(Number(slot.dataset.position));
});

sentenceGapsPreview.addEventListener("click", (event) => {
    const slot = event.target.closest(".sentence-insert-slot");

    if (slot) {
        if (placingToken) {
            insertPlacingToken(Number(slot.dataset.position));
        }

        return;
    }

    const zeroGap = event.target.closest(".sentence-zero-gap");

    if (zeroGap) {
        removeZeroGap(Number(zeroGap.dataset.position));
        return;
    }

    const mark = event.target.closest(".sentence-inserted-mark");

    if (mark) {
        removeInsertedMark(Number(mark.dataset.position));
        return;
    }

    const token = event.target.closest(".sentence-gap-token");

    if (!token || token.disabled) {
        return;
    }

    toggleSentenceGap(token);
});

backSentenceGapsButton.addEventListener("click", () => {
    clearPlacingToken();
    uploadCsvModal.classList.remove("is-sentence-gaps");
    uploadCsvModal.classList.add("is-sentence-form");
});

saveSentenceGapsButton.addEventListener("click", async () => {
    saveSentenceGapsButton.disabled = true;

    try {
        const responseData = await sentenceRequest(getSentenceSaveUrl(), {
            answer: sentenceAnswerInput.value.trim(),
            prompt: sentencePromptInput.value.trim(),
            // Все наборы: gaps, zero_gaps, marks копируем для сортировки от меньшего к больше
            gaps: sentenceFormState.gaps.slice().sort((a, b) => a - b),
            zero_gaps: sentenceFormState.zeroGaps.slice().sort((a, b) => a - b),
            marks: sentenceFormState.marks.slice().sort((a, b) => a.position - b.position)
        });

        renderSentencesList(responseData.data);
        closeSentenceForm();
    } catch (error) {
        showMessage(error.message);
        updateSaveSentenceGapsButton();
    }
});


function renderSentenceGaps(tokens) {
    sentenceGapsTokens = tokens;
    sentenceGapsPreview.replaceChildren();

    for (let position = 0; position <= tokens.length; position++) {
        sentenceGapsPreview.append(createInsertedItem(position));

        if (position === tokens.length) {
            break;
        }

        sentenceGapsPreview.append(createSentenceGapToken(tokens[position]));
    }

    updateSaveSentenceGapsButton();
}

function createInsertedItem(position) {

    if (sentenceFormState.zeroGaps.includes(position)) {
        return createZeroGap(position);
    }

    const mark = sentenceFormState.marks.find(
        (item) => item.position === position);

    if (mark) {
        return createInsertedMark(mark);
    }

    return createInsertSlot(position);
}

function createSentenceGapToken(token) {
    const button = sentenceGapTokenTemplate.content.firstElementChild.cloneNode(true);

    button.textContent = token.text;
    button.dataset.index = token.index;

    if (token.is_word) {
        button.classList.toggle("is-gap", sentenceFormState.gaps.includes(token.index));
    } else {
        button.disabled = true;
    }

    return button;
}

function createZeroGap(position) {
    const zeroGap = sentenceZeroGapTemplate.content.firstElementChild.cloneNode(true);

    zeroGap.dataset.position = position;

    return zeroGap;
}

function createInsertedMark(mark) {
    const button = sentenceInsertedMarkTemplate.content.firstElementChild.cloneNode(true);

    button.textContent = mark.text;
    button.dataset.position = mark.position;

    return button;
}

function createInsertSlot(position) {
    const slot = sentenceInsertSlotTemplate.content.firstElementChild.cloneNode(true);

    slot.dataset.position = position;

    return slot;
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
    updateSaveSentenceGapsButton();
}

function insertPlacingToken(position) {

    if (placingToken.kind === "zero") {
        sentenceFormState.zeroGaps.push(position);
    } else {
        sentenceFormState.marks.push({
            position: position,
            text: placingToken.text
        });
    }

    clearPlacingToken();
    renderSentenceGaps(sentenceGapsTokens);
}

function removeZeroGap(position) {
    sentenceFormState.zeroGaps = sentenceFormState.zeroGaps.filter(
        (item) => item !== position
    );

    renderSentenceGaps(sentenceGapsTokens);
}

function removeInsertedMark(position) {
    sentenceFormState.marks = sentenceFormState.marks.filter(
        (item) => item.position !== position
    );

    renderSentenceGaps(sentenceGapsTokens);
}

function setPlacingToken(token) {
    clearPlacingToken();

    placingToken = {
        kind: token.dataset.kind,
        text: token.dataset.token
    };
}

function clearPlacingToken() {
    placingToken = null;

    for (const token of sentenceGapsPalette.querySelectorAll(".is-selected")) {
        token.classList.remove("is-selected");
    }
}

function setDropTarget(slot) {

    for (const item of sentenceGapsPreview.querySelectorAll(".is-drop-target")) {
        if (item !== slot) {
            item.classList.remove("is-drop-target");
        }
    }

    slot.classList.add("is-drop-target");
}

function updateSaveSentenceGapsButton() {
    const gapsCount = sentenceFormState.gaps.length + sentenceFormState.zeroGaps.length;

    saveSentenceGapsButton.disabled = gapsCount === 0;
}