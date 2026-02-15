#from sqlalchemy import Column, Integer, String, ForeignKey
#from sqlalchemy.orm import relationship
#from app.database import Base


#class Broker(Base):
#    __tablename__ = "brokers"

#    id = Column(Integer, primary_key=True, index=True)
#    user_id = Column(Integer, ForeignKey("users.id"))
#    broker_name = Column(String, index=True)
 #   api_key = Column(String)      # encrypted
#    api_secret = Column(String)   # encrypted

#    user = relationship("User")
from pydantic import BaseModel

class BrokerCreate(BaseModel):
    broker_name: str
    api_key: str
    api_secret: str

# app/schemas.py
from pydantic import BaseModel
from typing import Optional

class BracketOrderRequest(BaseModel):
    symbol: str
    side: str
    size: float
    stop_loss: Optional[float] = None
    target: Optional[float] = None
