

async function lessonSaveRequest(editedData) {

    const lessonId = editedData.lessonId;
    const renamed = editedData.renamed;
    const deleted = editedData.deleted;

    const response = await fetch(
        `/courses/english/api/lessons/${lessonId}/tasks/`,
        {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.getElementsByName("csrfmiddlewaretoken")[0].value
            },
            body: JSON.stringify({
                renamed: renamed,
                deleted: deleted
            })
        }
    );

    const responseData = await response.json();

    if (!response.ok) {
        throw new Error(responseData.error ?? "Помилка під час запису на збереження змін уроку");
    }

    return responseData;
}
