const uploadCsvModal = document.getElementById("uploadCsvModal");
const uploadCsvInput = document.getElementById("uploadCsvInput");
const uploadCsvDropzone = document.getElementById("uploadCsvDropzone");
const uploadCsvFileName = document.getElementById("uploadCsvFileName");
const cancelUploadCsvButton = document.getElementById("cancelUploadCsvButton");
const confirmUploadCsvButton = document.getElementById("confirmUploadCsvButton");

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

    const importUrl = uploadCsvModal.dataset.importUrl;
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    setUploadCsvLoading(true);

    // const response = await fetch(importUrl, {
    //     method: "POST",
    //     headers: { "X-CSRFToken": csrfToken },
    //     body: formData,
    // });
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

// Отображение выбранного файла в модалке
function setSelectedFile(file) {
    uploadCsvDropzone.classList.toggle("has-file", Boolean(file));
    // Установка названия файла или стандартного текста
    // Стандартного текста - чтобы при следующем открытии модалки, 
    // она не имела следов предыдущей загрузки
    uploadCsvFileName.textContent = file ? `Файл: ${file.name}` : "Підтримується: .csv";
    confirmUploadCsvButton.disabled = !file;
}

function setUploadCsvLoading(isLoading) {
    uploadCsvModal.classList.toggle("is-loading", isLoading);
    confirmUploadCsvButton.disabled = isLoading || !uploadCsvInput.files[0];
}

function resetUploadCsvModal() {
    
    uploadCsvInput.value = "";
    setSelectedFile(null);
    setUploadCsvLoading(false);
}
