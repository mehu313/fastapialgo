from fastapi import APIRouter
from app.main import manager

router = APIRouter(prefix="/admin/strategy", tags=["Admin Strategy"])

@router.post("/start/{strategy_name}")
async def start(strategy_name: str):
    await manager.start_strategy(strategy_name)
    return {"message": f"{strategy_name} started"}

@router.post("/stop/{strategy_name}")
async def stop(strategy_name: str):
    await manager.stop_strategy(strategy_name)
    return {"message": f"{strategy_name} stopped"}
