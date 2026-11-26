import { createSentenceBuilder } from "../sentence_builder.js";
import { createSentenceFillBuilder } from "../sentence_fill_builder.js";

const sentenceStepTemplate = document.getElementById("sentenceStepTemplate");
const sentenceBankTokenTemplate = document.getElementById("sentenceBankTokenTemplate");
const sentenceFillTextTemplate = document.getElementById("sentenceFillTextTemplate");
const sentenceFillGapTemplate = document.getElementById("sentenceFillGapTemplate");

const GAP_MARKER = "___";

let builder = null;
let isFillStep = false;

export const sentenceRenderer = {
    render(step, container, onAnswer) {
        const stepElement = sentenceStepTemplate.content.firstElementChild.cloneNode(true);
        const bank = stepElement.querySelector(".sentence-tokens");

        isFillStep = step.variant === "fill";

        stepElement.querySelector(".sentence-translation").textContent = step.prompt;

        step.tokens.forEach((text, index) => {
            bank.append(createBankToken(text, index));
        });

        if (isFillStep) {
            renderFillTemplate(stepElement, step.template);
        }

        container.replaceChildren(stepElement);

        builder = isFillStep
            ? createSentenceFillBuilder(stepElement)
            : createSentenceBuilder(stepElement);

        stepElement.querySelector(".sentence-check-button").addEventListener("click", () => {
            if (isFillStep) {
                submitFill(onAnswer);
            } else {
                submitSentence(onAnswer);
            }
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

function renderFillTemplate(stepElement, template) {
    const words = stepElement.querySelector(".sentence-build-words");

    for (const piece of template) {
        if (piece === GAP_MARKER) {
            const gap = sentenceFillGapTemplate.content.firstElementChild.cloneNode(true);

            words.append(gap);

            continue;
        }

        const text = sentenceFillTextTemplate.content.firstElementChild.cloneNode(true);

        text.querySelector(".sentence-token-text").textContent = piece;
        words.append(text);
    }
}

function submitFill(onAnswer) {
    let answers;

    try {
        answers = builder.getAnswers();
    } catch (error) {
        showMessage("Не вдалося перевірити речення");
        return;
    }

    if (answers.length === 0 || answers.some((answer) => !answer)) {
        showMessage("Заповніть усі пропуски");
        return;
    }

    onAnswer({answers: answers});
}