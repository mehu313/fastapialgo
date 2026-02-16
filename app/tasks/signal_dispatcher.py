from app.websocket.manager import manager # Import your manager
from app.tasks.order_executor import execute_order

async def dispatch_signal(signal: dict):
    strategy_name = signal["strategy"]
    users = redis_client.smembers(f"strategy:{strategy_name}:users")

    for user_id_bytes in users:
        user_id = int(user_id_bytes)
        
        # 1. Execute Order in background
        execute_order.delay(user_id, signal)
        
        # 2. Update UI via WebSocket
        await manager.send_to_user(user_id, signal)