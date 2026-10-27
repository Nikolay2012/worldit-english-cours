const messageModal = document.getElementById("messageModal");
const messageModalText = document.getElementById("messageModalText");

// в миллисекундах
const messageDuration = 3000;
let messageTimer = null;

function showMessage(text) {
    clearTimeout(messageTimer);

    messageModalText.textContent = text
    messageModal.classList.add("is-visible");

    messageTimer = setTimeout(() => {
        messageModal.classList.remove("is-visible");
    }, messageDuration);
}
