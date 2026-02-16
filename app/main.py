import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models.models import Base 

# 1. 🔥 IMPORTANT: Explicitly import models so SQLAlchemy sees them
from app.models.user import User
from app.models.strategy import Strategy 

from app.api import admin, auth
from app.routers import broker, strategy_api, websocket
from app.engine.strategy_manager import StrategyManager

app = FastAPI()

# 2. ✅ Now create tables (it will now find 'Strategy')
Base.metadata.create_all(bind=engine)

# 3. ✅ Store StrategyManager in app state
strat_manager = StrategyManager() 
app.state.strategy_manager = strat_manager

# CORS
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
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
app.include_router(websocket.router)