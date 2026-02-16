from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.security.jwt import decode_access_token
from app.websocket.manager import manager

router = APIRouter()

@router.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    # 1. Accept the connection immediately to satisfy the browser handshake
    await websocket.accept()
    
    token = websocket.query_params.get("token")
    payload = decode_access_token(token)
    user_id = payload.get("user_id") if payload else None

    if not user_id:
        # Close with policy violation code if unauthorized
        await websocket.close(code=1008)
        return

    # 2. Register the user with your manager
    await manager.connect(int(user_id), websocket) 
    
    try:
        while True:
            # Keep the loop alive to receive data or maintain the connection
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(int(user_id))