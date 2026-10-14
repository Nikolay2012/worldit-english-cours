const moduleInfoButtons = document.querySelectorAll(".module-info-button");
const moduleInfoModal = document.getElementById("moduleInfoModal");

console.log(moduleInfoModal);

moduleInfoButtons.forEach((button) => {
    
    
    
    button.addEventListener(
        "click", 
        () => {
            const moduleId = button.getAttribute('module-id');
            const moduleName = button.getAttribute('module-name');
            const moduleInfoTitle = document.getElementById("moduleInfoTitle");
        
            moduleInfoTitle.textContent = `Модуль №${moduleId}: ${moduleName}`
            openModal(moduleInfoModal);
        }
    );
});
