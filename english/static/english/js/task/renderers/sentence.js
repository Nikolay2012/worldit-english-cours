import { createSentenceBuilder } from "../sentence_builder.js";

const sentenceStepTemplate = document.getElementById("sentenceStepTemplate");
const sentenceBankTokenTemplate = document.getElementById("sentenceBankTokenTemplate");

let builder = null;

export const sentenceRenderer = {
    render(step, container, onAnswer) {
        const stepElement = sentenceStepTemplate.content.firstElementChild.cloneNode(true);
        const bank = stepElement.querySelector(".sentence-tokens");

        stepElement.querySelector(".sentence-translation").textContent = step.prompt;

        step.tokens.forEach((text, index) => {
            bank.append(createBankToken(text, index));
        });

        container.replaceChildren(stepElement);
        builder = createSentenceBuilder(stepElement);

        stepElement.querySelector(".sentence-check-button").addEventListener("click", () => {
            submitSentence(onAnswer);
        });
    },

    lock() {
        builder?.lock();
    },

    unlock() {
        builder?.unlock();
    },

    showResult(container, isCorrect) {
        container.querySelector(".sentence-answer-row")?.classList.add(
            isCorrect ? "is-correct" : "is-wrong"
        );
    }
};

function createBankToken(text, index) {
    const token = sentenceBankTokenTemplate.content.firstElementChild.cloneNode(true);

    token.dataset.id = index;
    token.dataset.token = text;
    token.querySelector(".sentence-token-text").textContent = text;

    return token;
}

function submitSentence(onAnswer) {
    let tokens;

    try {
        tokens = builder.getTokens();
    } catch (error) {
        showMessage("Не вдалося перевірити речення");
        return;
    }

    const validationError = validateSentence(tokens);

    if (validationError) {
        showMessage(validationError);
        return;
    }

    onAnswer({
        tokens: tokens});
}

function validateSentence(tokens) {

    if (tokens.length === 0) {
        return "Зберіть речення";
    }

    if (tokens.some((token) => !token.trim())) {
        return "Речення містить порожнє слово";
    }

    return null;
}