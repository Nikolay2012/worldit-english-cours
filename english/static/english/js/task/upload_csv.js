const uploadCsvModal = document.getElementById("uploadCsvModal");
const uploadCsvTitle = document.getElementById("uploadCsvTitle");
const uploadCsvInput = document.getElementById("uploadCsvInput");
const uploadCsvDropzone = document.getElementById("uploadCsvDropzone");
const uploadCsvFileName = document.getElementById("uploadCsvFileName");
const cancelUploadCsvButton = document.getElementById("cancelUploadCsvButton");
const confirmUploadCsvButton = document.getElementById("confirmUploadCsvButton");
const closeWordsListButton = document.getElementById("closeWordsListButton");
const uploadCsvList = document.getElementById("uploadCsvList");
const wordsCategoryTemplate = document.getElementById("wordsCategoryTemplate");
const wordRowTemplate = document.getElementById("wordRowTemplate");

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
        const responseData = await taskImportRequest(importUrl, formData);
        setUploadCsvList(true, responseData);
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
        uploadCsvFileName.textContent = "Підтримується: .csv";
        showMessage("Файл має бути у форматі .csv");
        return false;
    }

    // Если размер файла не превышает мегабайта
    if (file.size > 1 * 1024 * 1024) {
        uploadCsvFileName.textContent = "Підтримується: .csv";
        showMessage("Файл не може перевищувати 1 МБ");
        return false;
    }

    if (file.size === 0) {
        uploadCsvFileName.textContent = "Підтримується: .csv";
        showMessage("Неможливо завантажити порожній файл");
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

function setUploadCsvList(isList, responseData) {
    uploadCsvModal.classList.toggle("is-list", isList);
    uploadCsvModal.classList.remove("is-loading");
    uploadCsvTitle.textContent = isList ? "Список слів" : uploadCsvTitle.textContent.trim();

    if (responseData) {
        console.log(responseData["data"]);
        renderWordsList(responseData.data);
    }
}

function renderWordsList(categories) {
    uploadCsvList.replaceChildren();

    for (const category of categories) {
        uploadCsvList.append(createCategory(category));
    }
}

function createCategory(category) {
    const section = wordsCategoryTemplate.content.firstElementChild.cloneNode(true);

    // в значении, аналог capitalize
    section.querySelector(".words-category-title").textContent = category.category.charAt(0).toUpperCase() + category.category.slice(1)
    section.querySelector(".add-words-button").dataset.category = category.category;

    const list = section.querySelector(".words-list");
    for (const word of category.words) {
        list.append(createWordRow(word));
    }

    return section;
}

function createWordRow(word) {
    const item = wordRowTemplate.content.firstElementChild.cloneNode(true);
    const row = item.querySelector(".word-row");

    row.dataset.stepId = word.stepId;
    row.querySelector(".word-text").textContent = word.question.text;
    row.querySelector(".word-translation").textContent = word.translation;

    return item;
}

function resetUploadCsvModal() {
    uploadCsvInput.value = "";
    setSelectedFile(null);
    setUploadCsvLoading(false);
    setUploadCsvList(false);
}
