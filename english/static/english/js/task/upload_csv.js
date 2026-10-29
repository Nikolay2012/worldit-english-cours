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
const uploadCsvWordForm = document.getElementById("uploadCsvWordForm");
const wordInput = document.getElementById("wordInput");
const translationInput = document.getElementById("translationInput");
const cancelWordButton = document.getElementById("cancelWordButton");
const saveWordButton = document.getElementById("saveWordButton");
const imageSlots = uploadCsvWordForm.querySelectorAll(".upload-csv-image");
const uploadCsvCloseIcon = uploadCsvModal.querySelector(".closeModal");
const modalCover = document.getElementById("modalCover");


// Заголовки и подсказки
const CREATE_WORD_TITLE = "Додати нове слово";
const EDIT_WORD_TITLE = "Редагувати слово";
const DEFAULT_TITLE = "Завантаження списку слів";
const LIST_TITLE = "Список слів";
const DELETE_LIST_TITLE = "Видалити список слів?";
const DEFAULT_FILE_HINT = "Підтримується: .csv";

// Макс. размер csv - мегабайт, как MAX_CSV_SIZE на сервере
const MAX_CSV_SIZE = 1 * 1024 * 1024;
// Для загрузки картинок к словам
const MAX_IMAGE_SIZE = 2 * 1024 * 1024;
const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"];
const PLACEHOLDER_IMAGE_URL = uploadCsvModal.dataset.placeholderUrl;

const wordsByStepId = new Map();

let wordFormState = {
    mode: null, 
    stepId: null, 
    category: null
};
let imageStates = [];


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

    uploadCsvModal.classList.remove("is-confirm-delete", "is-create-word", "is-edit-word");
    confirmDeleteListButton.disabled = false;

    resetWordForm();
}

function renderWordsList(categories) {
    uploadCsvList.replaceChildren();
    wordsByStepId.clear();

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

    row.dataset.stepId = word.step_id;
    row.querySelector(".word-text").textContent = word.question.text;
    row.querySelector(".word-translation").textContent = word.translation;

    wordsByStepId.set(word.step_id, word);
    
    return item;
}

function openWordForm(mode, word) {
    resetWordForm();

    wordFormState.mode = mode;

    if (mode === "create") {
        wordFormState.category = word.category;
    } else {
        wordFormState.stepId = word.step_id;
        wordInput.value = word.question.text;
        translationInput.value = word.translation;

        for (const image of word.images) {
            if (!image.is_placeholder) {
                imageStates[image.order].previewUrl = image.url;
            }
        }
    }

    imageSlots.forEach((slot, order) => renderImageSlot(order));

    uploadCsvModal.classList.add(mode === "create" ? "is-create-word" : "is-edit-word");
    uploadCsvTitle.textContent = mode === "create" ? CREATE_WORD_TITLE : EDIT_WORD_TITLE;
}

function closeWordForm() {
    uploadCsvModal.classList.remove("is-create-word", "is-edit-word");
    uploadCsvTitle.textContent = LIST_TITLE;
    resetWordForm();
}

function resetWordForm() {
    for (const state of imageStates) {
        revokePreview(state.previewUrl);
    }

    wordFormState = {
        mode: null,
        stepId: null, 
        category: null
    };

    wordInput.value = "";
    translationInput.value = "";

    imageStates = [];
    imageSlots.forEach((slot, order) => {
        imageStates.push({
            action: "keep", 
            file: null, 
            previewUrl: null
        });
        renderImageSlot(order);
    });
}

function replaceImage(order, file) {
    revokePreview(imageStates[order].previewUrl);

    imageStates[order] = {
        action: "replace",
        file: file,
        previewUrl: URL.createObjectURL(file)
    };

    renderImageSlot(order);
}

function removeImage(order) {
    revokePreview(imageStates[order].previewUrl);

    imageStates[order] = {
        action: "remove",
        file: null,
        previewUrl: null
    };

    renderImageSlot(order);
}

function renderImageSlot(order) {
    const slot = imageSlots[order];
    const state = imageStates[order];

    slot.querySelector(".upload-csv-image-preview").src = state.previewUrl || PLACEHOLDER_IMAGE_URL;
    slot.classList.toggle("has-image", Boolean(state.previewUrl));
}

function revokePreview(url) {

    if (url && url.startsWith("blob:")) {
        URL.revokeObjectURL(url);
    }
}

function isValidImageFile(file) {
    const name = file.name.toLowerCase();

    if (!IMAGE_EXTENSIONS.some((extension) => name.endsWith(extension))) {
        showMessage("Зображення має бути у форматі .png, .jpg або .jpeg");

        return false;
    }

    if (file.size === 0) {
        showMessage("Неможливо завантажити порожній файл");

        return false;
    }

    if (file.size > MAX_IMAGE_SIZE) {
        showMessage("Зображення не може перевищувати 2 МБ");
        return false;
    }

    return true;
}

function isValidWordForm() {

    if (!wordInput.value.trim()) {
        showMessage("Введіть слово");
        return false;
    }

    if (!translationInput.value.trim()) {
        showMessage("Введіть переклад");
        return false;
    }

    return true;
}

function collectWordFormData() {
    const formData = new FormData();

    formData.append("word", wordInput.value.trim());
    formData.append("translation", translationInput.value.trim());

    if (wordFormState.mode === "create") {
        formData.append("category", wordFormState.category);
    }

    imageStates.forEach((state, order) => {
        if (state.action === "replace") {
            formData.append(`image_${order}`, state.file);
        }

        if (state.action === "remove" && wordFormState.mode === "edit") {
            formData.append(`remove_image_${order}`, "1");
        }
    });

    return formData;
}

function reloadIfListLoaded() {
    if (uploadCsvModal.classList.contains("is-list")) {
        window.location.reload();
    }
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

async function wordSaveRequest(url, formData) {

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        },
        body: formData
    });

    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(responseData.error || "Не вдалося зберегти слово");
    }

    return responseData;
}
