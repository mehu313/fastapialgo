from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    brokers = relationship("BrokerCredential", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")

    # 👇 choose ONE approach (recommended)
    role = Column(String, default="user")  # admin / user
