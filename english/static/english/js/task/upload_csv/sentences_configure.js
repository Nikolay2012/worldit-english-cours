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
    insertPlacingToken(
        Number(slot.dataset.position),
        Number(slot.dataset.index)
    );
});

sentenceGapsPreview.addEventListener("click", (event) => {
    const slot = event.target.closest(".sentence-insert-slot");

    if (slot) {
        if (placingToken) {
            insertPlacingToken(Number(slot.dataset.position), Number(slot.dataset.index));
        }

        return;
    }

    const insert = event.target.closest(".sentence-zero-gap, .sentence-inserted-mark");

    if (insert) {
        removeInsert(Number(insert.dataset.position), Number(insert.dataset.index));
        return;
    }

    const token = event.target.closest(".sentence-gap-token");

    if (!token || token.disabled) {
        return;
    }

    toggleSentenceGap(token);
});

// Переключение на режим назад, к основному режиму модалки создания/редактирования
// где сами предложения еще вводтся
// без выбора пропусков
backSentenceGapsButton.addEventListener("click", () => {
    clearPlacingToken();
    uploadCsvModal.classList.remove("is-sentence-gaps");
    uploadCsvModal.classList.add("is-sentence-form");
});

saveSentenceGapsButton.addEventListener("click", async () => {
    
    if (isOpenedFromSentencesPanel) {
        clearPlacingToken();
        returnToSentencesPanel(collectSentenceChange());
        return;
    }

    saveSentenceGapsButton.disabled = true;

    try {
        const responseData = await sentenceRequest(getSentenceSaveUrl(), {
            answer: sentenceAnswerInput.value.trim(),
            prompt: sentencePromptInput.value.trim(),
            // Все наборы: gaps, zero_gaps, marks копируем для сортировки от меньшего к больше
            gaps: sentenceFormState.gaps.slice().sort((a, b) => a - b),
            inserts: sentenceFormState.inserts
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
        const inserts = getInsertsAt(position);

        sentenceGapsPreview.append(createInsertSlot(position, 0));

        inserts.forEach((insert, index) => {
            sentenceGapsPreview.append(createInsertedItem(insert, index));
            sentenceGapsPreview.append(createInsertSlot(position, index + 1));
        });

        if (position === tokens.length) {
            break;
        }

        sentenceGapsPreview.append(createSentenceGapToken(tokens[position]));
    }

    updateSaveSentenceGapsButton();
}

function createInsertedItem(insert, index) {
    const item = insert.kind === "zero"
        ? sentenceZeroGapTemplate.content.firstElementChild.cloneNode(true)
        : sentenceInsertedMarkTemplate.content.firstElementChild.cloneNode(true);

    if (insert.kind === "mark") {
        item.textContent = insert.text;
    }

    item.dataset.position = insert.position;
    item.dataset.index = index;

    return item;
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

function createInsertSlot(position, index) {
    const slot = sentenceInsertSlotTemplate.content.firstElementChild.cloneNode(true);

    slot.dataset.position = position;
    slot.dataset.index = index;

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

function insertPlacingToken(position, index) {

    if (placingToken.kind === "zero" && hasZeroGapAt(position)) {
        showMessage("На цьому місці вже є нульовий артикль");
        clearPlacingToken();
        return;
    }

    sentenceFormState.inserts.splice(getInsertsOffset(position) + index, 0, {
        position: position,
        kind: placingToken.kind,
        text: placingToken.text
    });

    clearPlacingToken();
    renderSentenceGaps(sentenceGapsTokens);
}

function removeInsert(position, index) {
    sentenceFormState.inserts.splice(getInsertsOffset(position) + index, 1);
    renderSentenceGaps(sentenceGapsTokens);
}

function getInsertsAt(position) {
    return sentenceFormState.inserts.filter((insert) => insert.position === position);
}

function getInsertsOffset(position) {
    const offset = sentenceFormState.inserts.findIndex((insert) => insert.position >= position);

    return offset === -1 ? sentenceFormState.inserts.length : offset;
}

function hasZeroGapAt(position) {
    return getInsertsAt(position).some((insert) => insert.kind === "zero");
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
    const zeroGapsCount = sentenceFormState.inserts.filter(
        (insert) => insert.kind === "zero"
    ).length;

    saveSentenceGapsButton.disabled = sentenceFormState.gaps.length + zeroGapsCount === 0;
}
