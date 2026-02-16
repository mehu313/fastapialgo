# app/websocket/manager.py
from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Stores active connections by user_id
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        # We assume the connection is already accepted by the router for token validation
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: dict):
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)

manager = ConnectionManager()