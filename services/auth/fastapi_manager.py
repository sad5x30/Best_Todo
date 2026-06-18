import os
from typing import Optional

import dotenv
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport, JWTStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from database import get_db
from models.users import User

from fastapi_users.password import PasswordHelper
from pwdlib import PasswordHash, exceptions
from pwdlib .hashers.argon2 import Argon2Hasher

dotenv.load_dotenv()
SECRET = os.getenv("SECRET_KEY")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

password_hash = PasswordHash((
    Argon2Hasher(),
))

password_helper = PasswordHelper(password_hash)

class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")


async def get_user_db(session=Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db, password_helper)


cookie_transport = CookieTransport(
    cookie_name="best_cookies",
    cookie_max_age=3600,
    cookie_secure=COOKIE_SECURE,
    cookie_httponly=True,
    cookie_samesite="lax",
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)
