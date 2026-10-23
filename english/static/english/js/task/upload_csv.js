const uploadCsvModal = document.getElementById("uploadCsvModal");
const uploadCsvInput = document.getElementById("uploadCsvInput");
const uploadCsvDropzone = document.getElementById("uploadCsvDropzone");
const uploadCsvFileName = document.getElementById("uploadCsvFileName");
const uploadCsvError = document.getElementById("uploadCsvError");
const cancelUploadCsvButton = document.getElementById("cancelUploadCsvButton");
const confirmUploadCsvButton = document.getElementById("confirmUploadCsvButton");
const uploadButtons = document.querySelectorAll(".upload-button");

uploadButtons.forEach((button) => {
    button.addEventListener("click", () => {
        resetUploadCsvModal();
        openModal(uploadCsvModal);
    });
});

uploadCsvDropzone.addEventListener("click", () => {
    uploadCsvInput.click();
});

uploadCsvInput.addEventListener("change", () => {
    const file = uploadCsvInput.files[0];

    if (!file) {
        return;
    }

    const error = validateCsvFile(file);

    if (error) {
        showUploadCsvError(error);

        uploadCsvInput.value = "";
        setSelectedFile(null);

        return;
    }

    showUploadCsvError("");
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

    const importUrl = uploadCsvModal.dataset.importUrl;
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    setUploadCsvLoading(true);

    console.log(formData);

    // const response = await fetch(importUrl, {
    //     method: "POST",
    //     headers: { "X-CSRFToken": csrfToken },
    //     body: formData,
    // });
});

function validateCsvFile(file) {

    if (!file.name.toLowerCase().endsWith(".csv")) {
        return "Оберіть файл у форматі .csv";
    }

    if (file.size > 1 * 1024 * 1024) {
        return "Файл завеликий. Максимум — 1 МБ";
    }

    if (file.size === 0) {
        return "Файл порожній";
    }

    return "";
}

// Отображение выбранного файла в модалке
function setSelectedFile(file) {
    uploadCsvDropzone.classList.toggle("has-file", Boolean(file));
    uploadCsvFileName.textContent = file ? file.name : uploadCsvFileName.textContent.trim();
    confirmUploadCsvButton.disabled = !file;
}

function showUploadCsvError(message) {
    uploadCsvError.textContent = message;
}

function setUploadCsvLoading(isLoading) {
    uploadCsvModal.classList.toggle("is-loading", isLoading);
    confirmUploadCsvButton.disabled = isLoading || !uploadCsvInput.files[0];
}

function resetUploadCsvModal() {
    uploadCsvInput.value = "";

    setSelectedFile(null);
    showUploadCsvError("");
    setUploadCsvLoading(false);
}
