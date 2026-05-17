from collections import defaultdict

from fastapi import WebSocket


class TaskConnectionManager:
    def __init__(self):
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        connections = self._connections.get(user_id)
        if not connections:
            return

        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def broadcast_task_change(self, user_id: int, action: str, task_id: int | None = None):
        connections = list(self._connections.get(user_id, ()))
        if not connections:
            return

        payload = {
            "type": "task_changed",
            "action": action,
            "task_id": task_id,
        }

        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                self.disconnect(user_id, websocket)


task_connection_manager = TaskConnectionManager()
