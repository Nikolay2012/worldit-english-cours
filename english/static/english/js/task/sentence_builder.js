const placedTokenTemplate = document.getElementById("sentencePlacedTokenTemplate");

export function createSentenceBuilder(stepElement) {
    const sentenceTokens = stepElement.querySelector(".sentence-tokens");
    const sentenceBuildWords = stepElement.querySelector(".sentence-build-words");
    const sentenceCheckButton = stepElement.querySelector(".sentence-check-button");

    let activeDrag = null;
    let isLocked = false;

    sentenceTokens.addEventListener("dragstart", (event) => {
        const tokenContainer = event.target.closest(".sentence-token");

        if (isLocked || !tokenContainer || tokenContainer.classList.contains("is-used")) {
            return;
        }

        activeDrag = {
            tokenContainer: tokenContainer,
            token: null,
            placed: false,
            fromBuild: false
        };
    });

    sentenceBuildWords.addEventListener("dragstart", (event) => {
        const sentenceToken = event.target.closest(".sentence-token");

        if (isLocked || !sentenceToken) {
            return;
        }

        activeDrag = {
            tokenContainer: getSource(sentenceToken),
            token: sentenceToken,
            placed: false,
            fromBuild: true
        };
    });

    sentenceBuildWords.addEventListener("dragover", (event) => {

        if (!activeDrag) {
            return;
        }

        event.preventDefault();

        if (!activeDrag.token) {
            activeDrag.token = createPlacedToken(activeDrag.tokenContainer);
        }

        const before = getInsertBefore(event.clientX, activeDrag.token);
        sentenceBuildWords.insertBefore(activeDrag.token, before);
        refreshPlacedTokens();
    });

    sentenceBuildWords.addEventListener("dragleave", (event) => {

        if (!activeDrag || activeDrag.fromBuild || !activeDrag.token || activeDrag.placed) {
            return;
        }

        if (sentenceBuildWords.contains(event.relatedTarget)) {
            return;
        }

        activeDrag.token.remove();
        activeDrag.token = null;
        refreshPlacedTokens();
    });

    sentenceBuildWords.addEventListener("drop", (event) => {

        if (!activeDrag) {
            return;
        }

        event.preventDefault();

        activeDrag.placed = true;
        markSourceUsed(activeDrag.tokenContainer);

        updateBuild();
    });

    stepElement.addEventListener("dragend", () => {

        if (!activeDrag) {
            return;
        }

        if (!activeDrag.placed && activeDrag.token) {
            activeDrag.token.remove();

            if (activeDrag.fromBuild) {
                releaseSource(activeDrag.tokenContainer);
            }
        }

        activeDrag = null;
        updateBuild();
    });

    sentenceTokens.addEventListener("click", (event) => {
        const source = event.target.closest(".sentence-token");

        if (isLocked || !source || source.classList.contains("is-used")) {
            return;
        }

        sentenceBuildWords.append(createPlacedToken(source));
        markSourceUsed(source);
        updateBuild();
    });

    sentenceBuildWords.addEventListener("click", (event) => {
        const token = event.target.closest(".sentence-token");

        if (isLocked || !token) {
            return;
        }

        releaseSource(getSource(token));
        token.remove();
        updateBuild();
    });

    function createPlacedToken(tokenContainer) {
        const token = placedTokenTemplate.content.firstElementChild.cloneNode(true);

        token.querySelector(".sentence-token-text").textContent = tokenContainer.dataset.token;
        token.dataset.sourceId = tokenContainer.dataset.id;
        token.dataset.token = tokenContainer.dataset.token;
        token.classList.toggle("is-mark", !/[\p{L}\p{N}]/u.test(tokenContainer.dataset.token));

        return token;
    }

    function getSource(token) {
        return sentenceTokens.querySelector(`[data-id="${token.dataset.sourceId}"]`);
    }

    function getInsertBefore(x, dragged) {
        const items = [...sentenceBuildWords.querySelectorAll(".sentence-token")]
            .filter((item) => item !== dragged);

        return items.find((item) => {
            const box = item.getBoundingClientRect();

            return x < box.left + box.width / 2;
        }) || null;
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
        sentenceCheckButton.disabled = isLocked || sentenceBuildWords.querySelector(".sentence-token") === null;
    }

    function setTokensDraggable(isDraggable) {

        for (const token of sentenceBuildWords.querySelectorAll(".sentence-token")) {
            token.draggable = isDraggable;
        }

        for (const token of sentenceTokens.querySelectorAll(".sentence-token")) {
            token.draggable = isDraggable && !token.classList.contains("is-used");
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

    function getTokens() {
        return [...sentenceBuildWords.querySelectorAll(".sentence-token-text")].map(
            (text) => text.textContent
        );
    }

    function refreshPlacedTokens() {
        const tokens = sentenceBuildWords.querySelectorAll(".sentence-token");

        tokens.forEach((token, index) => {
            const text = token.dataset.token;

            token.querySelector(".sentence-token-text").textContent = index === 0
                ? text.charAt(0).toUpperCase() + text.slice(1)
                : text;
        });
    }

    function updateBuild() {
        refreshPlacedTokens();
        updateCheckButton();
    }

    return {
        lock: lock,
        unlock: unlock,
        getTokens: getTokens
    };
    
}
