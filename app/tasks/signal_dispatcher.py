# app/tasks/signal_dispatcher.py
from app.websocket.manager import manager
from app.tasks.order_executor import execute_order
from app.services.redis_client import redis_client # Ensure redis_client is imported
import asyncio

async def dispatch_signal(signal: dict):
    """
    Dispatches a trading signal to all subscribed users via 
    Celery (for execution) and WebSockets (for UI updates).
    """
    strategy_name = signal.get("strategy")
    if not strategy_name:
        print("Signal received without a strategy name")
        return

    # Retrieve all user IDs subscribed to this specific strategy from Redis
    users = redis_client.smembers(f"strategy:{strategy_name}:users")

    if not users:
        # If no users are subscribed, we can still log the signal for the system
        print(f"No users subscribed to {strategy_name}. Signal ignored.")
        return

    # Create a list of WebSocket tasks to run them in parallel
    ws_tasks = []

    for user_id_bytes in users:
        try:
            # Convert bytes from Redis to integer
            user_id = int(user_id_bytes)
            
            # 1. Execute Order in background via Celery
            # .delay() pushes the task to the worker queue immediately
            execute_order.delay(user_id, signal)
            
            # 2. Prepare UI update via WebSocket
            # We add this to a task list to send them all at once
            ws_tasks.append(manager.send_to_user(user_id, signal))
            
        except (ValueError, TypeError) as e:
            print(f"Error processing user_id {user_id_bytes}: {e}")

    # Run all WebSocket updates concurrently to ensure low latency
    if ws_tasks:
        await asyncio.gather(*ws_tasks, return_exceptions=True)

    print(f"📢 Signal for {strategy_name} dispatched to {len(users)} users.")