# 🚀 Best_Todo — Real-Time FastAPI Application

Современный асинхронный веб-сервис для управления задачами в реальном времени. Проект построен на FastAPI, использует SQLAlchemy для работы с БД, миграции Alembic, а также Redis для кэширования и мгновенной синхронизации данных.

## 🛠 Технологический стек

* **Backend:** Python 3.10+, FastAPI (Asynchronous Framework)
* **Database:** SQLAlchemy (ORM), Alembic (Миграции)
* **Caching & Real-time:** Redis (Синхронизация событий, кэширование, очереди)
* **Frontend:** HTML5, CSS3, JavaScript (Реал-тайм обновление через WebSockets)
* **DevOps:** Docker, Docker Compose (Контейнеризация)
* **Testing:** Pytest (Автоматическое тестирование)

---
## скрины
![Главный экран](screenshots/home_page.png)
![логин](screenshots/login.png)
![регестрация](screenshots/register.png)
![создание задачи](screenshots/creating_task.png)

## 📂 Структура проекта

* `app_tests/` — тесты для проверки бизнес-логики и API эндпоинтов.
* `database/` — сессии и конфигурация подключения к базе данных.
* `migrations/` — файлы миграций Alembic.
* `models/` — ORM-модели (пользователи, задачи).
* `routes/` — маршруты API (FastAPI Router).
* `services/` — слой бизнес-логики приложения.
* `static/` & `templates/` — фронтенд (CSS, JS) и HTML-шаблоны (Jinja2).
* `redis_client.py` — клиент для асинхронного взаимодействия с Redis.
* `main.py` — точка входа (FastAPI ASGI application).

---

## ⚙️ Настройка окружения (.env)

Перед запуском проекта создайте файл `.env` в корневой директории и заполните его следующими переменными:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/todo_db
TEST_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/test_todo_db
SECRET_KEY=your_super_secret_key_here
REDIS_URL=redis://localhost:6379/0
COOKIE_SECURE=False  # True для Production (HTTPS), False для локальной разработки
```

---

## 🚀 Как запустить проект

### Вариант 1: Запуск через Docker (Рекомендуемый)

Убедитесь, что у вас установлены [Docker](https://docker.com) и Docker Compose.

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com
   cd Best_Todo
   ```
2. Создайте и заполните файл `.env`.
3. Запустите контейнеры одной командой:
   ```bash
   docker-compose up --build
   ```
   Сервис автоматически поднимет FastAPI приложение, базу данных PostgreSQL и Redis.

### Вариант 2: Локальный запуск (Разработка)

1. Клонируйте репозиторий и создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Linux/macOS
   venv\Scripts\activate     # Для Windows
   ```
2. Установите все зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Убедитесь, что локальные инстансы PostgreSQL и Redis запущены.
4. Примените миграции базы данных:
   ```bash
   alembic upgrade head
   ```
5. Запустите сервер разработки:
   ```bash
   uvicorn main:app --reload
   ```

---

## 🧪 Тестирование

Для запуска тестов выполните команду в виртуальном окружении:
```bash
pytest
```

---

## 💡 Функционал в планах (Roadmap)
- [ ] Разделение задач по пользовательским категориям и тегам.
- [ ] Добавление системы push-уведомлений.
- [ ] Интеграция напоминаний через Telegram-бота.

