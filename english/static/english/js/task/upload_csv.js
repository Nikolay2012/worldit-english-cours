const uploadCsvModal = document.getElementById("uploadCsvModal");
const uploadCsvTitle = document.getElementById("uploadCsvTitle");
const uploadCsvInput = document.getElementById("uploadCsvInput");
const uploadCsvDropzone = document.getElementById("uploadCsvDropzone");
const uploadCsvFileName = document.getElementById("uploadCsvFileName");
const cancelUploadCsvButton = document.getElementById("cancelUploadCsvButton");
const confirmUploadCsvButton = document.getElementById("confirmUploadCsvButton");
const closeWordsListButton = document.getElementById("closeWordsListButton");
const deleteWordsListButton = document.getElementById("deleteWordsListButton");
const cancelDeleteListButton = document.getElementById("cancelDeleteListButton");
const confirmDeleteListButton = document.getElementById("confirmDeleteListButton");
const uploadCsvList = document.getElementById("uploadCsvList");
const wordsCategoryTemplate = document.getElementById("wordsCategoryTemplate");
const wordRowTemplate = document.getElementById("wordRowTemplate");

// Заголовки и подсказки
const DEFAULT_TITLE = "Завантаження списку слів";
const LIST_TITLE = "Список слів";
const DELETE_LIST_TITLE = "Видалити список слів?";
const DEFAULT_FILE_HINT = "Підтримується: .csv";

// Макс. размер csv - мегабайт, как MAX_CSV_SIZE на сервере
const MAX_CSV_SIZE = 1 * 1024 * 1024;

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

function isValidCsvFile(file) {

    if (!file.name.toLowerCase().endsWith(".csv")) {
        showMessage("Файл має бути у форматі .csv");
        return false;
    }

    if (file.size === 0) {
        showMessage("Неможливо завантажити порожній файл");
        return false;
    }

    if (file.size > MAX_CSV_SIZE) {
        showMessage("Файл не може перевищувати 1 МБ");
        return false;
    }

    return true;
}

function setSelectedFile(file) {
    uploadCsvDropzone.classList.toggle("has-file", Boolean(file));
    uploadCsvFileName.textContent = file ? `Файл: ${file.name}` : DEFAULT_FILE_HINT;
    confirmUploadCsvButton.disabled = !file;
}

function setUploadCsvLoading(isLoading) {
    uploadCsvModal.classList.toggle("is-loading", isLoading);
    confirmUploadCsvButton.disabled = isLoading || !uploadCsvInput.files[0];
}

function setUploadCsvList(isList, responseData) {
    uploadCsvModal.classList.toggle("is-list", isList);
    uploadCsvModal.classList.remove("is-loading");
    uploadCsvTitle.textContent = isList ? LIST_TITLE : DEFAULT_TITLE;

    if (responseData) {
        renderWordsList(responseData.data);
    }
}

function setUploadCsvConfirmDelete(isConfirm) {
    uploadCsvModal.classList.toggle("is-confirm-delete", isConfirm);
    uploadCsvTitle.textContent = isConfirm ? DELETE_LIST_TITLE : LIST_TITLE;
}

function resetUploadCsvModal() {
    uploadCsvInput.value = "";
    setSelectedFile(null);
    setUploadCsvLoading(false);
    setUploadCsvList(false);
    uploadCsvModal.classList.remove("is-confirm-delete");
    confirmDeleteListButton.disabled = false;
}

function renderWordsList(categories) {
    uploadCsvList.replaceChildren();

    for (const category of categories) {
        uploadCsvList.append(createCategory(category));
    }
}

function createCategory(category) {
    const section = wordsCategoryTemplate.content.firstElementChild.cloneNode(true);

    // Аналог capitalize
    section.querySelector(".words-category-title").textContent =
        category.category.charAt(0).toUpperCase() + category.category.slice(1);
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

async function deleteTaskStepsRequest(url) {
    const response = await fetch(url, {
        method: "DELETE",
        headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        }
    });

    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(responseData.error || "Не вдалося видалити список");
    }
}
