const openTheoryModalButton = document.getElementById("openTheoryModalButton");
const theoryModal = document.getElementById("theoryModal");
const closeTheoryModalIcon = document.getElementById("closeTheoryModalIcon");
const closeTheoryModalButton = document.getElementById("closeTheoryModalButton");

if (openTheoryModalButton) {
    openTheoryModalButton.addEventListener("click", (event) => {
        openModal(theoryModal);
    });
}

if (closeTheoryModalIcon) {
    closeTheoryModalIcon.addEventListener("click", (event) => {
        closeModal();
    });
}

if (closeTheoryModalButton) {
    closeTheoryModalButton.addEventListener("click", (event) => {
        closeModal();
    });
}