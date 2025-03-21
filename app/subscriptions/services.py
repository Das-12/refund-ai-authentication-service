from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from .models import Plans, Subscription
from .schemas import PlanCreate, PlanUpdate, SubscriptionCreate, SubscriptionUpdate
from ..auth import decode_access_token, get_user
from ..permissions.permissions import has_permission
from datetime import datetime
from app.database import get_db

### Plans

def create_plan_service(plan_data: PlanCreate, token: str, db: Session):
    username = decode_access_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "create_plan"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    new_plan = Plans(**plan_data.model_dump())
    
    try:
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
    
    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    
    return new_plan

def list_plans_service(token: str, db: Session):
    print(f"started list plan in auth and this is {token}")
    username = decode_access_token(token)
    print(f"this is username {username}")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "view_plans"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return db.query(Plans).all()

def get_plan_by_id_service(plan_id: int, token: str, db: Session):
    username = decode_access_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "view_plans"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    plan = db.query(Plans).filter(Plans.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plans not found",
        )
    return plan

def update_plan_service(plan_id: int, plan_data: PlanUpdate, token: str, db: Session):
    username = decode_access_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "update_plan"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    plan = db.query(Plans).filter(Plans.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    update_data = {key: value for key, value in plan_data.model_dump(exclude_unset=True).items()}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    try:
        for key, value in update_data.items():
            setattr(plan, key, value)

        db.commit()
        db.refresh(plan)

    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

    return plan



def delete_plan_service(plan_id: int, token: str, db: Session):
    username = decode_access_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "delete_plan"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    delete = db.query(Plans).filter(Plans.id == plan_id).first()
    delete.is_deleted = True
    db.commit()
    db.refresh(delete)
    
    return {"message": "Plan deleted successfully"}


### Subscriptions

def create_subscription_service(subscription_data: SubscriptionCreate, token: str, db: Session):
    username = decode_access_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "create_subscription"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    plan = db.query(Plans).filter(Plans.id == subscription_data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    new_subscription = Subscription(
        company_id=subscription_data.company_id,
        plan_id=subscription_data.plan_id,
        start_date=subscription_data.start_date or datetime.now(),
    )

    try: 
        db.add(new_subscription)
        db.commit()
        db.refresh(new_subscription)
    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    
    return new_subscription

def list_subscriptions_service(token: str, db: Session):
    username = decode_access_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "view_subscriptions"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return db.query(Subscription).all()

def get_subscription_service(subscription_id: int, token: str, db: Session):
    username = decode_access_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "view_subscriptions"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    return subscription

def update_subscription_service(subscription_id: int, subscription_data: SubscriptionUpdate, token: str, db: Session):
    username = decode_access_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "update_subscription"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    update_data = {key: value for key, value in subscription_data.model_dump(exclude_unset=True).items()}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    try:
        for key, value in update_data.items():
            setattr(subscription, key, value)

        db.commit()
        db.refresh(subscription)

    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

    return subscription

def delete_subscription_service(subscription_id: int, token: str, db: Session):
    username = decode_access_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )

    user = get_user(db, username=username)
    
    if not has_permission(user, "delete_subscription"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    db.query(Subscription).filter(Subscription.id == subscription_id).delete()
    db.commit()
    
    return {"message": "Subscription deleted successfully"}        