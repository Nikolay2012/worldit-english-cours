const sentencesPanel = document.getElementById("sentencesPanel");
const sentencesPanelCover = document.getElementById("sentencesPanelCover");
const sentencesPanelBody = document.getElementById("sentencesPanelBody");
const closeSentencesPanelButton = document.getElementById("closeSentencesPanelButton");
const closeSentencesPanelFooterButton = document.getElementById("closeSentencesPanelFooterButton");
const deleteSentencesPanelListButton = document.getElementById("deleteSentencesPanelListButton");
const sentencesPanelRowTemplate = document.getElementById("sentencesPanelRowTemplate");
const sentencesPanelEmptyTemplate = document.getElementById("sentencesPanelEmptyTemplate");
const sentencesPanelAddTemplate = document.getElementById("sentencesPanelAddTemplate");

const canEditSentences = sentencesPanel?.dataset.canEdit === "true";

let isSentencesPanelLoading = false;


if (sentencesPanel) {
    for (const button of document.querySelectorAll("[data-open-sentences-panel]")) {
        button.addEventListener("click", () => {
            setSentencesPanelOpen(true);
            loadSentencesPanel();
        });
    }

    closeSentencesPanelButton.addEventListener("click", () => {
        setSentencesPanelOpen(false);
    });

    sentencesPanelCover.addEventListener("click", () => {
        setSentencesPanelOpen(false);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && sentencesPanel.classList.contains("is-open")) {
            setSentencesPanelOpen(false);
        }
    });

    if (canEditSentences) {
        closeSentencesPanelFooterButton.addEventListener("click", () => {
            setSentencesPanelOpen(false);
        });

        deleteSentencesPanelListButton.addEventListener("click", () => {
            document.dispatchEvent(new CustomEvent("sentencesPanelDelete"));
        });

        sentencesPanelBody.addEventListener("click", (event) => {
            if (event.target.closest(".sentences-panel-add-button")) {
                document.dispatchEvent(new CustomEvent("sentencesPanelCreate"));
                return;
            }

            const row = event.target.closest(".sentences-panel-row.is-editable");

            if (row) {
                document.dispatchEvent(new CustomEvent("sentencesPanelEdit", {
                    detail: {
                        stepId: Number(row.dataset.stepId)
                    }
                }));
            }
        });
    }
}

function setSentencesPanelOpen(isOpen) {
    sentencesPanel.classList.toggle("is-open", isOpen);
    sentencesPanelCover.classList.toggle("is-open", isOpen);
    document.body.classList.toggle("is-words-panel-open", isOpen);
}

function setSentencesPanelLoading(isLoading) {
    isSentencesPanelLoading = isLoading;
    sentencesPanel.classList.toggle("is-loading", isLoading);
}

async function loadSentencesPanel() {

    if (isSentencesPanelLoading) {
        return;
    }

    setSentencesPanelLoading(true);

    try {
        const data = await sentencesPanelRequest(
            sentencesPanel.dataset.sentencesProgressUrl
        );

        renderSentencesPanel(data.sentences);
    } catch (error) {
        showMessage(error.message);
    } finally {
        setSentencesPanelLoading(false);
    }
}

function renderSentencesPanel(sentences) {
    sentencesPanelBody.replaceChildren();

    if (sentences.length === 0) {
        const empty = sentencesPanelEmptyTemplate.content.firstElementChild.cloneNode(true);

        empty.textContent = sentencesPanel.dataset.emptyText;
        sentencesPanelBody.append(empty);
    } else {
        const list = document.createElement("ul");

        list.className = "words-panel-list";

        for (const sentence of sentences) {
            list.append(createSentencesPanelRow(sentence));
        }

        sentencesPanelBody.append(list);
    }

    if (canEditSentences) {
        sentencesPanelBody.append(
            sentencesPanelAddTemplate.content.firstElementChild.cloneNode(true)
        );
    }
}

function createSentencesPanelRow(sentence) {
    const row = sentencesPanelRowTemplate.content.firstElementChild.cloneNode(true);

    renderSentenceText(
        row.querySelector(".sentences-panel-text"),
        sentence.parts
    );
    row.title = sentence.answer;

    if (canEditSentences) {
        row.classList.add("is-editable");
        row.dataset.stepId = sentence.step_id;
    }

    return row;
}

async function sentencesPanelRequest(url) {
    const response = await fetch(url);
    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(responseData.error || "Не вдалося отримати список речень");
    }

    return responseData.data;
}