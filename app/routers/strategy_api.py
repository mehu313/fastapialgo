from fastapi import APIRouter
from pydantic import BaseModel
from app.services.redis_client import redis_client

router = APIRouter(prefix="/strategy", tags=["Strategy"])


class SubscribeRequest(BaseModel):
    user_id: int
    strategy_name: str
    broker_name: str
    api_key: str
    api_secret: str
    symbol: str
    qty: int
    sl: float
    target: float


class UnsubscribeRequest(BaseModel):
    user_id: int
    strategy_name: str


@router.post("/subscribe")
def subscribe(data: SubscribeRequest):

    # Add user to strategy set
    redis_client.sadd(f"strategy:{data.strategy_name}:users", data.user_id)

    # Store user config
    redis_client.hset(f"user:{data.user_id}:config", mapping={
        "broker": data.broker_name,
        "api_key": data.api_key,
        "api_secret": data.api_secret,
        "symbol": data.symbol,
        "qty": data.qty,
        "sl": data.sl,
        "target": data.target,
    })

    return {"message": "Subscribed successfully"}


@router.post("/unsubscribe")
def unsubscribe(data: UnsubscribeRequest):

    redis_client.srem(f"strategy:{data.strategy_name}:users", data.user_id)

    return {"message": "Unsubscribed successfully"}


@router.get("/subscribers/{strategy_name}")
def get_subscribers(strategy_name: str):

    users = redis_client.smembers(f"strategy:{strategy_name}:users")

    return {"users": list(users)}
