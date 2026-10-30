// Кнопка "Завантажити"
document.addEventListener("click", (event) => {
    if (!event.target.closest(".upload-button")) {
        return;
    }

    resetUploadCsvModal();
    openModal(uploadCsvModal);
});

uploadCsvDropzone.addEventListener("click", () => {
    uploadCsvInput.click();
});

uploadCsvInput.addEventListener("change", () => {
    const file = uploadCsvInput.files[0];
    if (!file) {
        return;
    }

    if (!isValidCsvFile(file)) {
        uploadCsvInput.value = "";
        setSelectedFile(null);
        return;
    }

    setSelectedFile(file);
});

cancelUploadCsvButton.addEventListener("click", () => {
    resetUploadCsvModal();
    closeModal();
});

confirmUploadCsvButton.addEventListener("click", async () => {
    const file = uploadCsvInput.files[0];
    if (!file) {
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploadCsvLoading(true);

    try {
        const responseData = await taskImportRequest(
            uploadCsvModal.dataset.importUrl, 
            formData
        );
        setUploadCsvList(true, responseData);
    } catch (error) {
        showMessage(error.message);
        setUploadCsvLoading(false);
    }
});

// Кнопка «Закрити» в списке слов
closeWordsListButton.addEventListener("click", () => {
    closeModal();
    // После загрузки задание уже не пустое,
    // потому обновляем страницу для отображения нового контента
    window.location.reload();
});

// Кнопка «Видалити список» - переход в режим подтверждения удаления списка слов
deleteWordsListButton.addEventListener("click", () => {
    setUploadCsvConfirmDelete(true);
});

// «Скасувати» в подтверждении удаления списка - возврат к списку
cancelDeleteListButton.addEventListener("click", () => {
    setUploadCsvConfirmDelete(false);
});

confirmDeleteListButton.addEventListener("click", async () => {
    // Чтобы не было двойного клика при запросе
    confirmDeleteListButton.disabled = true;

    try {
        await deleteTaskStepsRequest(uploadCsvModal.dataset.deleteUrl);
        window.location.reload();
    } catch (error) {
        showMessage(error.message);
        confirmDeleteListButton.disabled = false;
    }
});

uploadCsvList.addEventListener("click", (event) => {
    const button = event.target.closest(".add-words-button");
    
    if (!button) {
        return;
    }

    openWordForm(
        "create", 
        {
            category: button.dataset.category
        }
    );
});

uploadCsvList.addEventListener("click", (event) => {
    const row = event.target.closest(".word-row");

    if (!row) {
        return;
    }

    const word = wordsByStepId.get(Number(row.dataset.stepId));

    if (!word) {
        return;
    }

    openWordForm("edit", word);
});

uploadCsvWordForm.addEventListener("click", (event) => {
    const slot = event.target.closest(".upload-csv-image");
    
    if (!slot) {
        return;
    }

    if (event.target.closest(".upload-csv-image-delete")) {
        removeImage(Number(slot.dataset.order));

        return;
    }

    if (event.target.closest(".upload-csv-image-box")) {
        slot.querySelector(".upload-csv-image-input").click();
    }
});

uploadCsvWordForm.addEventListener("change", (event) => {
    const input = event.target.closest(".upload-csv-image-input");

    if (!input) {
        return;
    }

    const file = input.files[0];
    const order = Number(input.closest(".upload-csv-image").dataset.order);

    input.value = "";

    if (!file || !isValidImageFile(file)) {
        return;
    }

    replaceImage(order, file);
});

cancelWordButton.addEventListener("click", () => {
    closeWordForm();
});

saveWordButton.addEventListener("click", async () => {

    if (!isValidWordForm()) {
        return;
    }

    const url = wordFormState.mode === "create"
        ? uploadCsvModal.dataset.createWordUrl
        : uploadCsvModal.dataset.updateWordUrl.replace(/0\/$/, `${wordFormState.stepId}/`);

    saveWordButton.disabled = true;

    try {
        const responseData = await wordSaveRequest(url, collectWordFormData());
        renderWordsList(responseData.data);
        closeWordForm();
    } catch (error) {
        showMessage(error.message);
    } finally {
        saveWordButton.disabled = false;
    }
});

uploadCsvCloseIcon.addEventListener("click", () => {
    reloadIfListLoaded();
});

modalCover.addEventListener("mousedown", (event) => {
    
    if (event.target !== modalCover) {
        return;
    }

    reloadIfListLoaded();
});
