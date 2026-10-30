
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
