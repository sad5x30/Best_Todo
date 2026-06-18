from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/registration.html")


@router.get("/auth/login", response_class=HTMLResponse, include_in_schema=False)
async def auth_login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@router.get("/auth/register", response_class=HTMLResponse, include_in_schema=False)
async def auth_register_page(request: Request):
    return templates.TemplateResponse(request, "auth/registration.html")

@router.post("/logout", response_class=HTMLResponse)
async def logout():
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("best_cookies")
    return response
