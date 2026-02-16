# app/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager

# 1. Define the router instance BEFORE using it in decorators
router = APIRouter()

# 2. Use the simplified logic for testing as we discussed
@router.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the handshake immediately
    await websocket.accept()
    
    # Get user_id from query params (simple version for now)
    user_id = websocket.query_params.get("user_id", "1")

    # Register connection with the manager
    await manager.connect(int(user_id), websocket) 
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(int(user_id))