const taskRun = document.getElementById("taskRun");
const taskRunStep = document.getElementById("taskRunStep");

loadNextStep();

async function loadNextStep() {
    const response = await fetch(taskRun.dataset.nextStepUrl);
    const responseData = await response.json();

    console.log(responseData);

    taskRunStep.textContent = JSON.stringify(responseData.data);
}
