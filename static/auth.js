function getErrorMessage(detail, fallback) {
    if (typeof detail === "string") {
        return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
        return detail[0].msg || fallback;
    }

    if (detail && typeof detail === "object") {
        return detail.reason || detail.message || fallback;
    }

    return fallback;
}

function setMessage(node, text, type) {
    node.textContent = text;
    node.className = `message ${type} is-visible`;
}

function clearMessage(node) {
    node.textContent = "";
    node.className = "message";
}

async function submitAuthForm(form) {
    const mode = form.dataset.mode;
    const message = document.querySelector("[data-auth-message]");
    const button = form.querySelector("button[type='submit']");
    const defaultButtonText = button.textContent;

    clearMessage(message);
    button.disabled = true;
    button.textContent = mode === "login" ? "Входим..." : "Создаем аккаунт...";

    try {
        let response;

        if (mode === "login") {
            const formData = new FormData(form);
            const params = new URLSearchParams(formData);

            response = await fetch("/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: params,
            });
        } else {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            response = await fetch("/auth/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
        }

        if (response.ok) {
            if (mode === "login") {
                window.location.href = "/";
                return;
            }

            setMessage(message, "Аккаунт создан. Сейчас перенаправим на вход.", "success");
            setTimeout(() => {
                window.location.href = "/login";
            }, 700);
            return;
        }

        const payload = await response.json().catch(() => ({}));
        const fallback = mode === "login"
            ? "Неверный email или пароль."
            : "Не получилось создать аккаунт. Проверьте данные и попробуйте снова.";

        setMessage(message, getErrorMessage(payload.detail, fallback), "error");
    } catch (error) {
        setMessage(message, "Сервер не ответил. Проверьте подключение и попробуйте еще раз.", "error");
    } finally {
        button.disabled = false;
        button.textContent = defaultButtonText;
    }
}

document.querySelectorAll("[data-auth-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        submitAuthForm(form);
    });
});
