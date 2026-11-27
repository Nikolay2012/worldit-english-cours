const sentencesPanel = document.getElementById("sentencesPanel");
const sentencesPanelCover = document.getElementById("sentencesPanelCover");
const sentencesPanelBody = document.getElementById("sentencesPanelBody");
const closeSentencesPanelButton = document.getElementById("closeSentencesPanelButton");
const saveSentencesPanelButton = document.getElementById("saveSentencesPanelButton");
const deleteSentencesPanelListButton = document.getElementById("deleteSentencesPanelListButton");
const sentencesPanelRowTemplate = document.getElementById("sentencesPanelRowTemplate");
const sentencesPanelEmptyTemplate = document.getElementById("sentencesPanelEmptyTemplate");
const sentencesPanelAddTemplate = document.getElementById("sentencesPanelAddTemplate");

const canEditSentences = sentencesPanel?.dataset.canEdit === "true";

const sentencesPanelByKey = new Map();
const pendingSentenceChanges = new Map();

let sentencesPanelData = [];
let editingSentenceKey = null;
let newSentenceCounter = 0;

let isSentencesPanelLoading = false;


if (sentencesPanel) {
    for (const button of document.querySelectorAll("[data-open-sentences-panel]")) {
        button.addEventListener("click", () => {
            setSentencesPanelOpen(true);

            if (pendingSentenceChanges.size === 0) {
                loadSentencesPanel();
            }
        });
    }

    closeSentencesPanelButton.addEventListener("click", () => {
        setSentencesPanelOpen(false);
    });

    sentencesPanelCover.addEventListener("click", () => {
        setSentencesPanelOpen(false);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape" || !sentencesPanel.classList.contains("is-open")) {
            return;
        }

        if (canEditSentences && isOpenedFromSentencesPanel) {
            return;
        }

        setSentencesPanelOpen(false);
    });

    if (canEditSentences) {
        deleteSentencesPanelListButton.addEventListener("click", () => {
            openUploadCsvFromSentencesPanel("delete");
        });

        saveSentencesPanelButton.addEventListener("click", () => {
            if (pendingSentenceChanges.size === 0) {
                setSentencesPanelOpen(false);
                return;
            }

            console.log(buildSentencesBatchData());
        });

        sentencesPanelBody.addEventListener("click", (event) => {
            if (event.target.closest(".sentences-panel-add-button")) {
                newSentenceCounter += 1;
                editingSentenceKey = `new-${newSentenceCounter}`;

                openUploadCsvFromSentencesPanel("create", {
                    isFill: isSentencesPanelFill()
                });
                return;
            }

            const row = event.target.closest(".sentences-panel-row.is-editable");

            if (!row) {
                return;
            }

            const item = sentencesPanelByKey.get(row.dataset.sentenceKey);

            editingSentenceKey = row.dataset.sentenceKey;

            openUploadCsvFromSentencesPanel(item.mode, {
                sentence: item.sentence,
                change: item.change,
                isFill: isSentencesPanelFill()
            });
        });

        document.addEventListener("sentencesPanelReturn", (event) => {
            const change = event.detail?.change;

            if (change && editingSentenceKey) {
                pendingSentenceChanges.set(editingSentenceKey, change);
                renderSentencesPanel();
            }

            editingSentenceKey = null;
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

        sentencesPanelData = data.sentences;
        renderSentencesPanel();
    } catch (error) {
        showMessage(error.message);
    } finally {
        setSentencesPanelLoading(false);
    }
}

function renderSentencesPanel() {
    sentencesPanelBody.replaceChildren();
    sentencesPanelByKey.clear();

    const list = document.createElement("ul");

    list.className = "words-panel-list";

    for (const sentence of sentencesPanelData) {
        const key = String(sentence.step_id);

        list.append(createSentencesPanelRow(
            key,
            sentence,
            pendingSentenceChanges.get(key)
        ));
    }

    for (const [key, change] of pendingSentenceChanges) {
        if (change.mode === "create") {
            list.append(createSentencesPanelRow(key, null, change));
        }
    }

    if (list.children.length === 0) {
        const empty = sentencesPanelEmptyTemplate.content.firstElementChild.cloneNode(true);

        empty.textContent = sentencesPanel.dataset.emptyText;
        sentencesPanelBody.append(empty);
    } else {
        sentencesPanelBody.append(list);
    }

    if (canEditSentences) {
        sentencesPanelBody.append(
            sentencesPanelAddTemplate.content.firstElementChild.cloneNode(true)
        );
    }
}

function createSentencesPanelRow(key, sentence, change) {
    const row = sentencesPanelRowTemplate.content.firstElementChild.cloneNode(true);
    const text = row.querySelector(".sentences-panel-text");

    if (change) {
        text.textContent = change.data.answer;
        row.title = change.data.answer;
    } else {
        renderSentenceText(text, sentence.parts);
        row.title = sentence.answer;
    }

    if (canEditSentences) {
        row.classList.add("is-editable");
        row.classList.toggle("is-changed", Boolean(change));
        row.dataset.sentenceKey = key;

        sentencesPanelByKey.set(key, {
            mode: sentence ? "edit" : "create",
            sentence: sentence,
            change: change
        });
    }

    return row;
}

function isSentencesPanelFill() {
    return sentencesPanelData.some((sentence) => Boolean(sentence.template));
}

function buildSentencesBatchData() {
    const changes = [];

    for (const [key, change] of pendingSentenceChanges) {
        changes.push({
            key: key,
            mode: change.mode,
            step_id: change.stepId,
            data: change.data
        });
    }

    return {
        changes: changes
    };
}

async function sentencesPanelRequest(url) {
    const response = await fetch(url);
    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(responseData.error || "Не вдалося отримати список речень");
    }

    return responseData.data;
}