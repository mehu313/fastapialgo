from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models.models import Base

# 🔥 Import models (so SQLAlchemy registers them)
from app.models import user
from app.models import strategy as strategy_model

# API routers
from app.api import admin, auth
from app.routers import broker
from app.routers import strategy_api

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(strategy_api.router)
app.include_router(broker.router)
