from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from database import async_session
from models.users import User
from services.auth.fastapi_manager import UserManager, get_jwt_strategy, password_helper
from services.task_realtime import task_connection_manager


router = APIRouter()


async def get_websocket_user(websocket: WebSocket):
    token = websocket.cookies.get("boba")
    if not token:
        return None

    async with async_session() as session:
        user_db = SQLAlchemyUserDatabase(session, User)
        user_manager = UserManager(user_db, password_helper)
        strategy = get_jwt_strategy()
        return await strategy.read_token(token, user_manager)


@router.websocket("/ws/tasks")
async def tasks_websocket(websocket: WebSocket):
    user = await get_websocket_user(websocket)
    if user is None or not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await task_connection_manager.connect(user.id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        task_connection_manager.disconnect(user.id, websocket)
