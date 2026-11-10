const openTheoryModalButton = document.getElementById("openTheoryModalButton");
const theoryModal = document.getElementById("theoryModal");
const closeTheoryModalIcon = document.getElementById("closeTheoryModalIcon");
const closeTheoryModalButton = document.getElementById("closeTheoryModalButton");

openTheoryModalButton.addEventListener("click", (event) => {
    openModal(theoryModal);
});

closeTheoryModalIcon.addEventListener("click", (event) => {
    closeModal();
});

closeTheoryModalButton.addEventListener("click", (event) => {
    closeModal();
});