
export const questionRenderer = {
    render(step, container, onAnswer) {
        const stepTemplate = document.getElementById("questionStepTemplate");
        const optionTemplate = document.getElementById("questionOptionTemplate");

        const stepElement = stepTemplate.content.firstElementChild.cloneNode(true);
        const prompt = stepElement.querySelector(".question-step-prompt");

        if (step.prompt.kind === "image") {
            prompt.classList.add("is-image");
            stepElement.querySelector(".question-step-image").src = step.prompt.url;
        } else {
            prompt.classList.add("is-text");
            stepElement.querySelector(".question-step-word").textContent = step.prompt.text;
        }

        const optionsContainer = stepElement.querySelector(".question-step-options");

        for (const option of step.options) {
            const button = optionTemplate.content.firstElementChild.cloneNode(true);

            button.textContent = option.text;
            button.dataset.optionId = option.id;

            optionsContainer.append(button);
        }

        optionsContainer.addEventListener("click", (event) => {
            const button = event.target.closest(".question-step-option");

            if (!button || button.disabled) {
                return;
            }

            button.classList.add("is-selected");
            onAnswer({
                option_id: Number(button.dataset.optionId)
            });
        });

        container.replaceChildren(stepElement);
    },

    // блокируем кнопки ответов
    // блокируем до того момента, пока сервером не будет дан ответ
    lock(container) {
        for (const button of container.querySelectorAll(".question-step-option")) {
            button.disabled = true;
        }
    },

    // после даного сервером ответа разблокируем кнопки ответов (на новом шаге задания соотвественно)
    unlock(container) {
        for (const button of container.querySelectorAll(".question-step-option")) {
            button.disabled = false;
            button.classList.remove("is-selected");
        }
    },

    showResult(container, isCorrect) {
        const resultClass = isCorrect ? "is-correct" : "is-wrong";

        container.querySelector(".question-step").classList.add(resultClass);
        container.querySelector(".question-step-option.is-selected").classList.add(resultClass);
    }
}
