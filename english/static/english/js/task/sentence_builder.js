const sentenceTokens = document.querySelector(".sentence-tokens");
const sentenceBuildWords = document.getElementById("sentenceBuildWords");
const placedTokenTemplate = document.getElementById("sentencePlacedTokenTemplate");
const sentenceCheckButton = document.getElementById("sentenceCheckButton");

let activeDrag = null;

sentenceTokens.addEventListener("dragstart", (event) => {

    const tokenContainer = event.target.closest('.sentence-token');

    if (!tokenContainer || tokenContainer.classList.contains("is-used")) {
        return;
    }

    activeDrag = {
        tokenContainer: tokenContainer,
        token: null,
        placed: false,
        fromSentenceBuild: false
    };
});


sentenceBuildWords.addEventListener("dragover", (event) => {

    if (!activeDrag) {
        return;
    }

    event.preventDefault();

    if (!activeDrag.token){
        activeDrag.token = createPlacedToken(activeDrag.tokenContainer);
    }

    // индекс на который поставим новыйт окен предложения
    const before = getInsertBefore(event.clientX, activeDrag.token)
    sentenceBuildWords.insertBefore(activeDrag.token, before)
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

});

sentenceBuildWords.addEventListener("drop", (event) => {
    
    if (!activeDrag) {
        return;
    }
    
    event.preventDefault();

    activeDrag.placed = true;
    activeDrag.tokenContainer.classList.add('is-used');

    updateCheckButton();
})

sentenceBuildWords.addEventListener("dragstart", (event) => {
    const sentenceToken = event.target.closest(".sentence-token");

    if (!sentenceToken) {return;}

    activeDrag = {
        tokenContainer: getSource(sentenceToken),
        token: sentenceToken,
        placed: false,
        fromBuild: true
    };
});

sentenceBuildWords.addEventListener("click", (event) => {
    const removeButton = event.target.closest(".sentence-token-remove");

    if (!removeButton) {
        return;
    }

    const token = removeButton.closest(".sentence-token");

    getSource(token)?.classList.remove("is-used");
    token.remove();

    updateCheckButton();
});

// Если токен не был дотянут до области sentence-words-build
document.addEventListener("dragend", (event) => {

    if (!activeDrag) {
        return;
    }

    if (!activeDrag.placed) {
        // Удаление уже размещенных частей предложения, которые были вытянуты
        if (activeDrag.fromBuild) {
            activeDrag.token.remove();
            activeDrag.tokenContainer?.classList.remove('is-used');
        }
    }

    activeDrag = null;

    updateCheckButton();
})

function createPlacedToken(tokenContainer) {
    const token = placedTokenTemplate.content.firstElementChild.cloneNode(true);

    token.querySelector(".sentence-token-text").textContent = tokenContainer.dataset.token;
    token.dataset.sourceId = tokenContainer.dataset.id;

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

function updateCheckButton() {
    sentenceCheckButton.disabled = sentenceBuildWords.querySelector(".sentence-token") === null;
}