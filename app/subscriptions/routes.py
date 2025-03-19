from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from ..database import get_db
from .schemas import PlanCreate, PlanUpdate, SubscriptionCreate, SubscriptionUpdate
from .services import (
    create_plan_service,
    list_plans_service,
    get_plan_by_id_service,
    update_plan_service,
    delete_plan_service,
    create_subscription_service,
    list_subscriptions_service,
    get_subscription_service,
    update_subscription_service,
    delete_subscription_service
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

### Plans

@router.post("/plans", tags=["plans"])
async def create_plan(plan: PlanCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # print("plans in auth subscription started")
    try:
        return create_plan_service(plan, token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/plans", tags=["plans"])
async def list_plans(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        return list_plans_service(token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/plans/{plan_id}", tags=["plans"])
async def get_plan(plan_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        return get_plan_by_id_service(plan_id, token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/plans/{plan_id}", tags=["plans"])
async def update_plan(plan_id: int, plan: PlanUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        return update_plan_service(plan_id, plan, token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/plans/{plan_id}", tags=["plans"])
async def delete_plan(plan_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        return delete_plan_service(plan_id, token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

### Subscriptions

@router.post("/subscriptions", tags=["subscriptions"])
async def create_subscription(subscription: SubscriptionCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print("subscrition in subscription started")
    try:
        return create_subscription_service(subscription, token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/subscriptions", tags=["subscriptions"])
async def list_subscriptions(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        return list_subscriptions_service(token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/subscriptions/{subscription_id}", tags=["subscriptions"])
async def get_subscription(subscription_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        return get_subscription_service(subscription_id, token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/subscriptions/{subscription_id}", tags=["subscriptions"])
async def update_subscription(subscription_id: int, subscription: SubscriptionUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        return update_subscription_service(subscription_id, subscription, token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/subscriptions/{subscription_id}", tags=["subscriptions"])
async def delete_subscription(subscription_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        return delete_subscription_service(subscription_id, token, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")