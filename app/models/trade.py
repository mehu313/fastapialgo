from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String)
    side = Column(String)  # BUY / SELL
    price = Column(Float)
    quantity = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
