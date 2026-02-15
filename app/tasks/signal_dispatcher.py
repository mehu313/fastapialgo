from app.services.redis_client import redis_client
from app.tasks.order_executor import execute_order


async def dispatch_signal(signal: dict):

    strategy_name = signal["strategy"]

    users = redis_client.smembers(f"strategy:{strategy_name}:users")

    for user_id in users:
        execute_order.delay(int(user_id), signal)
