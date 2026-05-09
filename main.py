from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_users import FastAPIUsers

from models.users import User
from services.auth.auth_schemas import UserCreate, UserRead
from services.auth.fastapi_manager import auth_backend, get_user_manager


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/registration.html")


@app.get("/auth/login", response_class=HTMLResponse, include_in_schema=False)
async def auth_login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@app.get("/auth/register", response_class=HTMLResponse, include_in_schema=False)
async def auth_register_page(request: Request):
    return templates.TemplateResponse(request, "auth/registration.html")
