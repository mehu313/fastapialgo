import json
from celery import shared_task
from app.services.redis_client import redis_client
from app.brokers.factory import get_broker


@shared_task
def close_position(user_id, symbol):

    position_key = f"position:{user_id}:{symbol}"

    position_data = redis_client.get(position_key)
    if not position_data:
        return

    position = json.loads(position_data)

    config = redis_client.hgetall(f"user:{user_id}:config")
    if not config:
        return

    broker = get_broker(
        config["broker"],
        config["api_key"],
        config["api_secret"]
    )

    broker.square_off(symbol)

    redis_client.delete(position_key)

    print(f"🛑 Position CLOSED for user {user_id}")
