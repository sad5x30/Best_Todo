from fastapi_users import FastAPIUsers
from models.users import User
from services.auth.fastapi_manager import auth_backend, get_user_manager

TASK_PRIORITIES = {"low", "medium", "high"}
TASK_PRIORITY_LABELS = {
    "low": "Низкий",
    "medium": "Средний",
    "high": "Высокий",
}

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])
current_user = fastapi_users.current_user(optional=True)
current_active_user = fastapi_users.current_user()
