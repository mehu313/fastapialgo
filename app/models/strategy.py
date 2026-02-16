from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    strategy_name = Column(String)   # e.g. DUMMY, ORB
    symbol = Column(String)
    quantity = Column(Integer)

    stop_loss = Column(Float)
    target = Column(Float)

    is_running = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)

    user = relationship("User", back_populates="strategies")
from sqlalchemy.orm import relationship
# ...
class Strategy(Base):
    __tablename__ = "strategies"
    # Use the string "User" here
    user = relationship("User", back_populates="strategies")