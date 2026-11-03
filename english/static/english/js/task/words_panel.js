const wordsPanel = document.getElementById("wordsPanel");
const wordsPanelCover = document.getElementById("wordsPanelCover");
const openWordsPanelButton = document.getElementById("openWordsPanelButton");
const closeWordsPanelButton = document.getElementById("closeWordsPanelButton");

if (wordsPanel && openWordsPanelButton) {
    openWordsPanelButton.addEventListener("click", () => {
        setWordsPanelOpen(true);
    });

    closeWordsPanelButton.addEventListener("click", () => {
        setWordsPanelOpen(false);
    });

    wordsPanelCover.addEventListener("click", () => {
        setWordsPanelOpen(false);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && wordsPanel.classList.contains("is-open")) {
            setWordsPanelOpen(false);
        }
    });
}

function setWordsPanelOpen(isOpen) {
    wordsPanel.classList.toggle("is-open", isOpen);
    wordsPanelCover.classList.toggle("is-open", isOpen);
}