from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.redis_client import redis_client
import json
from typing import Dict, Any
router = APIRouter(prefix="/strategy", tags=["Strategy"])

# ================================ Models ================================

class SaveStrategyRequest(BaseModel):
    strategy_name: str
    parameters: Dict[str, Any]
    user_id: int

class StartStrategyRequest(BaseModel):
    user_id: int
    strategy_name: str

class StopStrategyRequest(BaseModel):
    user_id: int
    strategy_name: str

# ================================ Endpoints ================================

@router.post("/save")
def save_strategy(data: SaveStrategyRequest):
    if not data.strategy_name:
        raise HTTPException(status_code=400, detail="Strategy name required")
    key = f"user:{data.user_id}:strategy:{data.strategy_name}:config"
    redis_client.set(key, json.dumps(data.parameters))
    return {"status": "success", "message": f"{data.strategy_name} configuration saved successfully"}

from fastapi import APIRouter, HTTPException, Request # Add Request
# ... other imports

@router.post("/start")
async def start_strategy(data: StartStrategyRequest, request: Request):
    # 1. Check config in Redis as you already do
    key = f"user:{data.user_id}:strategy:{data.strategy_name}:config"
    config = redis_client.get(key)
    if not config:
        raise HTTPException(status_code=400, detail="Strategy configuration not saved")

    # 2. Update status in Redis
    redis_client.set(f"user:{data.user_id}:strategy:{data.strategy_name}:status", "running")
    redis_client.sadd(f"strategy:{data.strategy_name}:users", data.user_id)

    # 3. 🔥 CRITICAL: Start the actual loop in StrategyManager
    # We access the manager instance created in main.py
    await request.app.state.strategy_manager.start_strategy(data.strategy_name)
    
    return {"status": "success", "message": f"{data.strategy_name} started"}

@router.post("/stop")
def stop_strategy(data: StopStrategyRequest):
    redis_client.set(f"user:{data.user_id}:strategy:{data.strategy_name}:status", "stopped")
    redis_client.srem(f"strategy:{data.strategy_name}:users", data.user_id)
    return {"status": "success", "message": f"{data.strategy_name} stopped successfully"}

@router.get("/status/{user_id}/{strategy_name}")
def get_strategy_status(user_id: int, strategy_name: str):
    status = redis_client.get(f"user:{user_id}:strategy:{strategy_name}:status")
    if status:
        status = status.decode() if isinstance(status, bytes) else status
    return {"status": status if status == "running" else "stopped"}

@router.get("/available")
def get_available_strategies():
    return {
        "strategies": [
            {"name": "bollinger", "parameters": ["symbol", "qty", "sl", "target"]},
            {"name": "rsi", "parameters": ["symbol", "qty", "sl", "target", "period"]},
        ]
    }

@router.get("/saved/{user_id}")
def get_saved_strategies(user_id: int):
    keys = redis_client.keys(f"user:{user_id}:strategy:*:config")
    strategies = []
    for key in keys:
        key_str = key.decode() if isinstance(key, bytes) else key
        name = key_str.split(":")[3]
        params = redis_client.get(key)
        if params:
            params = json.loads(params.decode() if isinstance(params, bytes) else params)
            strategies.append({"strategy_name": name, "parameters": params})
    return {"strategies": strategies}

@router.delete("/delete")
def delete_strategy(user_id: int, strategy_name: str):
    redis_client.delete(f"user:{user_id}:strategy:{strategy_name}:config")
    redis_client.delete(f"user:{user_id}:strategy:{strategy_name}:status")
    redis_client.srem(f"strategy:{strategy_name}:users", user_id)
    return {"status": "success", "message": "Deleted successfully"}
