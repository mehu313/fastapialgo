import json
import time
from celery import shared_task
from app.services.redis_client import redis_client
from app.brokers.factory import get_broker

EXEC_LOCK_EXPIRY = 10  # seconds


@shared_task(bind=True, max_retries=3)
def execute_order(self, user_id, signal):

    strategy = signal["strategy"]
    symbol = signal["symbol"]
    side = signal["signal"]

    exec_lock_key = f"exec_lock:{user_id}:{strategy}:{symbol}"
    position_key = f"position:{user_id}:{symbol}"

    # ===============================
    # 1️⃣ EXECUTION LOCK (Race Safety)
    # ===============================
    lock_acquired = redis_client.set(
        exec_lock_key,
        "1",
        nx=True,
        ex=EXEC_LOCK_EXPIRY
    )

    if not lock_acquired:
        print(f"⚠ Execution skipped (race condition) user={user_id}")
        return

    try:
        # ===============================
        # 2️⃣ POSITION LOCK (Double Entry Protection)
        # ===============================
        if redis_client.exists(position_key):
            print(f"⚠ User {user_id} already in position for {symbol}")
            return

        config = redis_client.hgetall(f"user:{user_id}:config")
        if not config:
            print(f"⚠ No config found for user {user_id}")
            return

        broker = get_broker(
            config["broker"],
            config["api_key"],
            config["api_secret"]
        )

        qty = float(config["qty"])

        # ===============================
        # 3️⃣ PLACE ORDER
        # ===============================
        order_response = broker.place_order(
            symbol=symbol,
            side=side.lower(),
            qty=qty
        )

        entry_price = signal["price"]

        # ===============================
        # 4️⃣ SAVE POSITION STATE
        # ===============================
        position_data = {
            "strategy": strategy,
            "side": side,
            "entry_price": entry_price,
            "qty": qty,
            "timestamp": int(time.time())
        }

        redis_client.set(position_key, json.dumps(position_data))

        print(f"✅ Position OPENED for user {user_id}")

    except Exception as e:
        print(f"❌ Order failed user={user_id} → {e}")
        raise self.retry(exc=e, countdown=5)

    finally:
        # Release short race lock
        redis_client.delete(exec_lock_key)
