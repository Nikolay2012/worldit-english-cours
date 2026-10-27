

async function taskImportRequest(importUrl, formData) {
    
    const response = await fetch(
        importUrl, 
        {
            method: "POST",
            headers: {
                "X-CSRFToken": document.getElementsByName("csrfmiddlewaretoken")[0].value
            },
            body: formData,
        }
    );

    const responseData = await response.json();

    if (!response.ok) {
        throw new Error(responseData.error ?? "Помилка під час завантаження даних завдання");
    }

    return responseData;
}
