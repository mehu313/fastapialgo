import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models.models import Base   # import models
from app.api import admin, auth
from app.routers import broker
from app.models import user  # 👈 force import User model
from app.models import strategy 

from app.routers import strategy_api
from app.engine.strategy_manager import StrategyManager


app = FastAPI()
manager = StrategyManager()


# ✅ Create tables
Base.metadata.create_all(bind=engine)

# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    #allow_origins=["*"], 
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Routers 
app.include_router(admin.router) 
app.include_router(auth.router) 
app.include_router(strategy_api.router) 
app.include_router(broker.router)
#@app.on_event("startup")
#async def startup():

#    if not manager.running_strategies:
#        await manager.start_strategy("bollinger")
#        await manager.start_strategy("rsi")

#    print("🚀 Strategy Engine Started")

#@app.on_event("shutdown")
#async def shutdown():

#    for strategy_name in list(manager.running_strategies.keys()):
#        await manager.stop_strategy(strategy_name)

#    print("🛑 All strategies stopped")
