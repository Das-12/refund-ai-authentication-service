from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from .database import Base
from pydantic import BaseModel
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    api_keys = relationship("APIKey", back_populates="owner")

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    owner = relationship("User", back_populates="api_keys")

class UserCreate(BaseModel):
    username: str
    password: str
