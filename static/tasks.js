const modal = document.querySelector("[data-task-modal]");
const taskForm = document.querySelector("[data-task-form]");
const modalTitle = document.querySelector("[data-modal-title]");
const modalSubmit = document.querySelector("[data-modal-submit]");
const titleInput = document.querySelector("#task-title");
const descriptionInput = document.querySelector("#task-description");
const deadlineInput = document.querySelector("#task-deadline");
const doneInput = document.querySelector("[data-done-input]");
const priorityInputs = document.querySelectorAll("[data-priority-input]");
let realtimeReloadTimer = null;
let realtimeSocket = null;

function scheduleRealtimeReload(delay = 120) {
    window.clearTimeout(realtimeReloadTimer);
    realtimeReloadTimer = window.setTimeout(() => {
        window.location.reload();
    }, delay);
}

function connectTaskSocket() {
    if (!taskForm || !window.WebSocket) {
        return;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    realtimeSocket = new WebSocket(`${protocol}://${window.location.host}/ws/tasks`);

    realtimeSocket.addEventListener("message", (event) => {
        let payload = null;

        try {
            payload = JSON.parse(event.data);
        } catch {
            return;
        }

        if (payload?.type === "task_changed") {
            scheduleRealtimeReload();
        }
    });

    realtimeSocket.addEventListener("close", () => {
        window.setTimeout(connectTaskSocket, 1500);
    });
}

function isTaskMutationForm(form) {
    if (!(form instanceof HTMLFormElement)) {
        return false;
    }

    const action = new URL(form.action, window.location.href);
    return form.method.toLowerCase() === "post" && action.pathname.startsWith("/tasks");
}

document.addEventListener("submit", async (event) => {
    const form = event.target;

    if (!isTaskMutationForm(form)) {
        return;
    }

    event.preventDefault();

    const submitter = event.submitter;
    submitter?.setAttribute("disabled", "");

    try {
        const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            credentials: "same-origin",
        });

        if (!response.ok) {
            throw new Error("Task request failed");
        }

        modal?.close();
        scheduleRealtimeReload(900);
    } catch {
        form.submit();
    } finally {
        submitter?.removeAttribute("disabled");
    }
});

function setPriority(priority) {
    const nextPriority = priority || "medium";

    priorityInputs.forEach((input) => {
        input.checked = input.value === nextPriority;
    });
}

function openTaskModal() {
    if (!modal) {
        return;
    }

    modal.showModal();
    window.setTimeout(() => titleInput?.focus(), 80);
}

function setCreateMode() {
    taskForm.action = "/tasks";
    modalTitle.textContent = "Новая задача";
    modalSubmit.textContent = "Добавить задачу";
    titleInput.value = "";
    descriptionInput.value = "";
    deadlineInput.value = "";
    doneInput.checked = false;
    setPriority("medium");
    openTaskModal();
}

function setEditMode(button) {
    const taskId = button.dataset.taskId;

    taskForm.action = `/tasks/${taskId}/edit`;
    modalTitle.textContent = "Редактирование";
    modalSubmit.textContent = "Сохранить изменения";
    titleInput.value = button.dataset.taskTitle || "";
    descriptionInput.value = button.dataset.taskDescription || "";
    deadlineInput.value = button.dataset.taskDeadline || "";
    doneInput.checked = button.dataset.taskDone === "true";
    setPriority(button.dataset.taskPriority);
    openTaskModal();
}

document.querySelectorAll("[data-open-task-modal]").forEach((button) => {
    button.addEventListener("click", setCreateMode);
});

document.querySelectorAll("[data-edit-task]").forEach((button) => {
    button.addEventListener("click", () => setEditMode(button));
});

document.querySelectorAll("[data-close-task-modal]").forEach((button) => {
    button.addEventListener("click", () => modal?.close());
});

modal?.addEventListener("click", (event) => {
    if (event.target === modal) {
        modal.close();
    }
});

modal?.addEventListener("cancel", () => {
    taskForm?.reset();
});

connectTaskSocket();
