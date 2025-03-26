from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from ..database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Company(Base):
    
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255))
    contact_person_name = Column(String(255))
    email = Column(String(255),unique=True,index=True)
    phone_number = Column(String(255),unique=True,index=True)
    secondary_phone_number = Column(String(255),unique=True,index=True)
    is_active = Column(Boolean, default=True, nullable=True)
    
    users = relationship("User", back_populates="company")
    api_keys = relationship("APIKey",uselist=False, back_populates="company", cascade="all, delete-orphan")
    
    subscription = relationship("Subscription", uselist=False, back_populates="company", cascade="all, delete-orphan")

class User(Base):
    
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    company_id = Column(Integer, ForeignKey('companies.id'))
    is_active = Column(Boolean, default=True, nullable=True)
    # Many-to-One relationship with Company
    company = relationship("Company", back_populates="users")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    subscription_counts = relationship("UserSubscriptionCount", back_populates="user", cascade="all, delete-orphan")

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    company = relationship("Company", back_populates="api_keys")

