
// Згортання категорії слів
uploadCsvList.addEventListener("click", (event) => {
    const button = event.target.closest(".words-category .collapse-button");
    
    if (!button) {
        return;
    }

    const category = button.closest(".words-category");
    const isCollapsed = category.classList.toggle("collapsed");

    button.setAttribute("aria-expanded", String(!isCollapsed));
    button.setAttribute("aria-label", isCollapsed ? "Розгорнути категорію" : "Згорнути категорію");
});
