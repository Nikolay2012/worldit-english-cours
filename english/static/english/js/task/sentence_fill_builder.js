const placedTokenTemplate = document.getElementById("sentencePlacedTokenTemplate");
const sentenceFillGapTemplate = document.getElementById("sentenceFillGapTemplate");


export function createSentenceFillBuilder(stepElement) {
    const sentenceTokens = stepElement.querySelector(".sentence-tokens");
    const sentenceFillWords = stepElement.querySelector(".sentence-build-words");
    const sentenceCheckButton = stepElement.querySelector(".sentence-check-button");

    let activeDrag = null;
    let isLocked = false;

    sentenceTokens.addEventListener("dragstart", (event) => {
        const source = event.target.closest(".sentence-token");

        if (isLocked || !source || source.classList.contains("is-used")) {
            return;
        }

        activeDrag = {
            source: source,
            fromGap: null,
            dropped: false
        };
    });

    sentenceFillWords.addEventListener("dragstart", (event) => {
        const gap = event.target.closest(".sentence-fill-gap");

        if (isLocked || !gap || gap.classList.contains("is-empty")) {
            return;
        }

        activeDrag = {
            source: getSource(gap),
            fromGap: gap,
            dropped: false
        };
    });

    sentenceFillWords.addEventListener("dragover", (event) => {
        const gap = event.target.closest(".sentence-fill-gap");

        if (!activeDrag || !gap) {
            return;
        }

        event.preventDefault();
        setDropTarget(gap);
    });

    sentenceFillWords.addEventListener("dragleave", (event) => {
        const gap = event.target.closest(".sentence-fill-gap");

        if (gap && !gap.contains(event.relatedTarget)) {
            gap.classList.remove("is-drop-target");
        }
    });

    sentenceFillWords.addEventListener("drop", (event) => {
        const gap = event.target.closest(".sentence-fill-gap");

        if (!activeDrag || !gap) {
            return;
        }

        event.preventDefault();
        activeDrag.dropped = true;

        if (gap === activeDrag.fromGap) {
            clearDropTargets();
            return;
        }

        if (activeDrag.fromGap) {
            clearGap(activeDrag.fromGap);
        }

        fillGap(gap, activeDrag.source);
    });

    stepElement.addEventListener("dragend", () => {

        if (activeDrag?.fromGap && !activeDrag.dropped) {
            clearGap(activeDrag.fromGap);
            updateCheckButton();
        }

        activeDrag = null;
        clearDropTargets();
    });

    sentenceTokens.addEventListener("click", (event) => {
        const source = event.target.closest(".sentence-token");

        if (isLocked || !source || source.classList.contains("is-used")) {
            return;
        }

        const gap = sentenceFillWords.querySelector(".sentence-fill-gap.is-empty");

        if (!gap) {
            return;
        }

        fillGap(gap, source);
    });

    sentenceFillWords.addEventListener("click", (event) => {
        const gap = event.target.closest(".sentence-fill-gap");

        if (isLocked || !gap || gap.classList.contains("is-empty")) {
            return;
        }

        clearGap(gap);
        updateCheckButton();
    });

    function fillGap(gap, source) {

        if (!gap.classList.contains("is-empty")) {
            clearGap(gap);
        }

        const token = placedTokenTemplate.content.firstElementChild.cloneNode(true);

        token.querySelector(".sentence-token-text").textContent = getGapText(gap, source.dataset.token);
        token.draggable = !isLocked;

        gap.replaceChildren(token);
        gap.dataset.sourceId = source.dataset.id;
        gap.dataset.token = source.dataset.token;
        gap.classList.remove("is-empty");

        markSourceUsed(source);
        clearDropTargets();
        updateCheckButton();
    }

    function clearGap(gap) {
        releaseSource(getSource(gap));

        delete gap.dataset.sourceId;
        delete gap.dataset.token;

        gap.classList.add("is-empty");
        gap.replaceChildren(createEmptyGapContent());
    }

    function createEmptyGapContent() {
        return sentenceFillGapTemplate.content.firstElementChild.firstElementChild.cloneNode(true);
    }

    function getGapText(gap, text) {

        if (gap !== sentenceFillWords.firstElementChild) {
            return text;
        }

        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    function getSource(gap) {

        if (!gap.dataset.sourceId) {
            return null;
        }

        return sentenceTokens.querySelector(`[data-id="${gap.dataset.sourceId}"]`);
    }

    function setDropTarget(gap) {

        for (const item of sentenceFillWords.querySelectorAll(".is-drop-target")) {
            if (item !== gap) {
                item.classList.remove("is-drop-target");
            }
        }

        gap.classList.add("is-drop-target");
    }

    function clearDropTargets() {

        for (const item of sentenceFillWords.querySelectorAll(".is-drop-target")) {
            item.classList.remove("is-drop-target");
        }
    }

    function markSourceUsed(source) {
        source.classList.add("is-used");
        source.draggable = false;
    }

    function releaseSource(source) {

        if (!source) {
            return;
        }

        source.classList.remove("is-used");
        source.draggable = true;
    }

    function updateCheckButton() {
        sentenceCheckButton.disabled = isLocked
            || sentenceFillWords.querySelector(".sentence-fill-gap.is-empty") !== null;
    }

    function setTokensDraggable(isDraggable) {

        for (const token of sentenceTokens.querySelectorAll(".sentence-token")) {
            token.draggable = isDraggable && !token.classList.contains("is-used");
        }

        for (const token of sentenceFillWords.querySelectorAll(".sentence-fill-gap:not(.is-empty) .sentence-token")) {
            token.draggable = isDraggable;
        }
    }

    function lock() {
        isLocked = true;
        setTokensDraggable(false);
        updateCheckButton();
    }

    function unlock() {
        isLocked = false;
        setTokensDraggable(true);
        updateCheckButton();
    }

    function getAnswers() {
        return [...sentenceFillWords.querySelectorAll(".sentence-fill-gap")].map(
            (gap) => gap.dataset.token ?? ""
        );
    }

    return {
        lock: lock,
        unlock: unlock,
        getAnswers: getAnswers
    };
}