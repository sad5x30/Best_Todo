const modal = document.querySelector("[data-task-modal]");
const taskForm = document.querySelector("[data-task-form]");
const modalTitle = document.querySelector("[data-modal-title]");
const modalSubmit = document.querySelector("[data-modal-submit]");
const titleInput = document.querySelector("#task-title");
const descriptionInput = document.querySelector("#task-description");
const deadlineInput = document.querySelector("#task-deadline");
const doneInput = document.querySelector("[data-done-input]");
const priorityInputs = document.querySelectorAll("[data-priority-input]");

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
