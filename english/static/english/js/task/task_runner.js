import { questionRenderer } from "./renderers/question.js";

const STEP_RENDERERS = {
    question: questionRenderer
};

const taskRun = document.getElementById("taskRun");
const taskRunStep = document.getElementById("taskRunStep");
const taskRunProgressBar = document.getElementById("taskRunProgressBar");
const taskRunProgressValue = document.getElementById("taskRunProgressValue");

const resultDelay = 3000;
const completeDelay = 2000;

let currentStep = null;
let currentRenderer = null;

loadFirstStep();

async function loadFirstStep() {
    try {
        const data = await nextStepRequest(null);
        showNextStep(data);

    } catch (error) {
        showMessage(error.message);
    }
}

function showNextStep(data) {
    renderProgress(data.progress);

    if (data.step === null) {
        completeTask();
        
        return;
    }

    const renderer = STEP_RENDERERS[data.step.kind];

    if (!renderer) {
        showMessage("Невідомий тип кроку");
        
        return;
    }
    
    currentStep = data.step;
    currentRenderer = renderer;

    renderer.render(
        data.step,
        taskRunStep,
        submitAnswer
    );
}

async function submitAnswer(answerData) {
    currentRenderer.lock(taskRunStep);

    let result;

    try {
        result = await answerRequest(
            currentStep.id,
            answerData
        );
    } catch (error) {
        showMessage(error.message);
        currentRenderer.unlock(taskRunStep);
        
        return;
    }

    currentRenderer.showResult(taskRunStep, result.is_correct);
    renderProgress(result.progress);

    try {
        const [data] = await Promise.all([
            nextStepRequest(currentStep.id),
            wait(resultDelay)
        ]);

        showNextStep(data);
    } catch (error) {
        showMessage(error.message);
    }
}

function wait(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function completeTask() {

    setTimeout(() => {
        window.location.href = taskRun.dataset.moduleUrl;
    }, completeDelay);
}

function renderProgress(progress) {
    
    if (!progress) {
        return;
    }

    taskRunProgressBar.style.width = `${progress.percent}%`;
    taskRunProgressValue.textContent = `${progress.percent}%`;
}

async function nextStepRequest(afterStepId) {

    const url = new URL(
        // указано в run.html
        taskRun.dataset.nextStepUrl,
        window.location.origin
    );

    if (afterStepId !== null) {
        url.searchParams.set("after", afterStepId);
    }

    const response = await fetch(url);
    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(
            responseData.error || "Не вдалося отримати крок"
        );
    }

    return responseData.data;
}

async function answerRequest(stepId, answerData) {

    // подставляем id шага заместо стандартного 0 в атрибуте data-answer-url
    // атрибут расположен в run.html
    const url = taskRun.dataset.answerUrl.replace("steps/0/", `steps/${stepId}/`);

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        },
        body: JSON.stringify(answerData)
    });

    const responseData = await response.json();

    if (!response.ok || !responseData.ok) {
        throw new Error(
            responseData.error || "Не вдалося надіслати відповідь"
        );
    }

    return responseData.data;
}
