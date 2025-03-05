from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, CheckConstraint, UniqueConstraint
from ..database import Base
from pydantic import BaseModel
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import pytz
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import validates
from app.auth.models import User, Company

IST = pytz.timezone("Asia/Kolkata")

class Plans(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    description = Column(String(255))
    price = Column(Integer)
    additional_price_per_request = Column(Integer)
    max_request = Column(Integer)
    type_of_subscription = Column(String(50))
    
    __table_args__ = (
        CheckConstraint("type_of_subscription IN ('monthly', 'yearly')", name="valid_subscription_type"),
    )
    
    subscriptions = relationship("Subscription", back_populates="plan")
    
    def __str__(self):
        return f"Plan name={self.name})"
    


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), unique=True)
    plan_id = Column(Integer, ForeignKey("plans.id"))
    start_date = Column(DateTime, default=lambda: datetime.now(IST))
    end_date = Column(DateTime, nullable=False)
    total_count = Column(Integer, default=0)

    company = relationship("Company", back_populates="subscription")
    plan = relationship("Plans", back_populates="subscriptions")

    def __init__(self, company_id, plan_id, start_date=None):
        self.company_id = company_id
        self.plan_id = plan_id
        self.start_date = start_date or datetime.now(IST)
        self.end_date = self.calculate_end_date(self.plan_id, self.start_date)

    def calculate_end_date(self, plan_id, start_date):
        """Fetches the plan and calculates end date."""
        from ..database import SessionLocal
        db = SessionLocal()
        plan = db.query(Plans).filter(Plans.id == plan_id).first()
        db.close()

        if plan and plan.type_of_subscription.lower() == "monthly":
            return start_date + timedelta(days=30)
        elif plan and plan.type_of_subscription.lower() == "yearly":
            return start_date + timedelta(days=365)
        return start_date

    @validates("plan_id")
    def validate_plan_id(self, key, value):
        """Recalculate end_date when plan_id is updated."""
        self.end_date = self.calculate_end_date(value, self.start_date)
        return value

    @validates("start_date")
    def validate_start_date(self, key, value):
        """Recalculate end_date when start_date is updated."""
        self.end_date = self.calculate_end_date(self.plan_id, value)
        return value

    def __str__(self):
        return f"Subscription(company_id={self.company_id}, plan_id={self.plan_id}, start_date={self.start_date}, end_date={self.end_date})"
    
class UserSubscriptionCount(Base):
    __tablename__ = "user_subscription_counts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    request_count = Column(Integer, default=0) 
    
    user = relationship("User", back_populates="subscription_counts")
    company = relationship("Company", back_populates="user_subscription_counts")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'month', 'year', name='unique_user_monthly_count'),
    )
    
User.subscription_counts = relationship("UserSubscriptionCount", back_populates="user", cascade="all, delete-orphan")
Company.user_subscription_counts = relationship("UserSubscriptionCount", back_populates="company", cascade="all, delete-orphan")