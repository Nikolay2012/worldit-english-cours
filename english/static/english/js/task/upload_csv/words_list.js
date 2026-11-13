document.addEventListener("uploadCsvImported", (event) => {
    renderWordsList(event.detail.data);
});

function renderWordsList(categories) {
    uploadCsvList.replaceChildren();
    wordsByStepId.clear();

    for (const category of categories) {
        uploadCsvList.append(createCategory(category));
    }
}
