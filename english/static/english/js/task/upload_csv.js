const uploadCsvModal = document.getElementById("uploadCsvModal");
const uploadCsvTitle = document.getElementById("uploadCsvTitle");
const uploadCsvInput = document.getElementById("uploadCsvInput");
const uploadCsvDropzone = document.getElementById("uploadCsvDropzone");
const uploadCsvFileName = document.getElementById("uploadCsvFileName");
const cancelUploadCsvButton = document.getElementById("cancelUploadCsvButton");
const confirmUploadCsvButton = document.getElementById("confirmUploadCsvButton");
const closeWordsListButton = document.getElementById("closeWordsListButton");

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

    const importUrl = uploadCsvModal.dataset.importUrl;

    try {
        await taskImportRequest(importUrl, formData);
        setUploadCsvList(true);
    } catch (error) {
        console.error(error);
        setUploadCsvLoading(false);
    }
});

// Кнопка "Закрыть" в списке слов (модалка списка слов)
closeWordsListButton.addEventListener("click", () => {
    closeModal();
    // После успешной загрузки данных задания оно, очевидно, уже не пустое
    // Потому обновляем страницу для отображения нового контента админу/ментора
    window.location.reload();
});

function isValidCsvFile(file) {
    
    if (!file.name.toLowerCase().endsWith(".csv")) {
        return false;
    }

    if (file.size > 1 * 1024 * 1024) {
        return false;
    }

    if (file.size === 0) {
        return false;
    }

    return true;
}

function setSelectedFile(file) {
    uploadCsvDropzone.classList.toggle("has-file", Boolean(file));
    uploadCsvFileName.textContent = file ? `Файл: ${file.name}` : uploadCsvFileName.textContent.trim();
    confirmUploadCsvButton.disabled = !file;
}

function setUploadCsvLoading(isLoading) {
    uploadCsvModal.classList.toggle("is-loading", isLoading);
    confirmUploadCsvButton.disabled = isLoading || !uploadCsvInput.files[0];
}

function setUploadCsvList(isList) {
    uploadCsvModal.classList.toggle("is-list", isList);
    uploadCsvModal.classList.remove("is-loading");
    uploadCsvTitle.textContent = isList ? "Список слів" : uploadCsvTitle.textContent.trim();
}

function resetUploadCsvModal() {
    uploadCsvInput.value = "";
    setSelectedFile(null);
    setUploadCsvLoading(false);
    setUploadCsvList(false);
}
