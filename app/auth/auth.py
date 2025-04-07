from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.orm import joinedload

from app.auth.request_models import CompanyCreate, UserOut
from .models import Company, User,APIKey
from ..config import settings
import secrets
from sqlalchemy.orm import Session
from app.auth.request_models import UserOut
from app.subscriptions.models import Subscription, UserSubscriptionCount
from sqlalchemy import func

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_api_key(db:Session):
    apiKey = secrets.token_hex(32)
    isExist = get_api_key(db,apiKey)
    if isExist:
        generate_api_key(db)
    return apiKey

def create_api_key(db: Session, user: User,expiry_minutes: int = 60*24*15):
    expiration_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    api_key = APIKey(key=generate_api_key(db), owner=user,expires_at=expiration_time)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key

def get_api_key(db: Session, key: str):
    api_key = db.query(APIKey).filter(APIKey.key == key).first()
    if api_key and api_key.expires_at > datetime.utcnow():
        return api_key
    return None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    print(f"decode access token started and this is token {token}")
        # print("try block started")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    print(f"this is payload: {payload}")
    username: str = payload.get("sub")
    if username is None:
       raise HTTPException(status_code=404, detail="user not found from token")
    return username

def get_user(db: Session, username: str):
    if username is not None:
        data = db.query(User).filter(User.username == username).first()
        return data
    else:
        raise HTTPException(status_code=404, detail="username not found")

def get_company(db: Session, phone_number: str):
    return db.query(Company).filter(Company.phone_number == phone_number).first()

def get_company_with_apikey(db: Session, token: str):
    apiKey = db.query(APIKey).filter(APIKey.key==token).first()
    return apiKey.company

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if user and user.is_active == False:
        return None
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_user(db: Session, username: str, password: str):
    hashed_password = get_password_hash(password)
    db_user = User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_company(db: Session, company:CompanyCreate):
    expiration_time = datetime.utcnow() + timedelta(days=150)  # 150 days from now

    # Create the API key instance
    api_key_instance = APIKey(
        key=generate_api_key(db),
        expires_at=expiration_time
    )

    db_company = Company(
        company_name=company.company_name,
        contact_person_name=company.contact_person_name,
        email=company.email,
        phone_number=company.phone_number,
        secondary_phone_number=company.secondary_phone_number,
        api_keys=api_key_instance
    )
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)

    return db_company

def is_api_key_valid(apiKeys:list[APIKey], key: str) -> bool:
    # Iterate over the user's API keys
    for api_key in apiKeys:
        # Check if the key matches
        if api_key.key == key:
            # Check if the key has expired
            if api_key.expires_at > datetime.utcnow():
                return True
            else:
                return False


def get_all_company(db: Session):
    data = db.query(Company).options(joinedload(Company.subscription)).all()
    for user in data:
        if user.is_active == False:
            data.remove(user)
    return [
        {
			"email": d.email,
			"phone_number": d.phone_number,
			"is_active": d.is_active,
			"id": d.id,
			"company_name": d.company_name,
			"contact_person_name": d.contact_person_name,
			"secondary_phone_number": d.secondary_phone_number,
            "hit_count": d.subscription.total_count if d.subscription else 0
		}
        for d in data
    ]


def get_company_by_id(company_id: int, db: Session):
    data = db.query(Company).filter(Company.id == company_id).first()
    if data.is_active == False:
        return None
    else:
        return data


def update_company(company_id: int, company: CompanyCreate, db: Session):
    db_company = db.query(Company).filter(Company.id == company_id).first()
    db_company.company_name = company.company_name
    db_company.contact_person_name = company.contact_person_name
    db_company.email = company.email
    db_company.phone_number = company.phone_number
    db_company.secondary_phone_number = company.secondary_phone_number
    db.commit()
    db.refresh(db_company)
    return db_company


def delete_company(company_id: int, db: Session):
    db_company = db.query(Company).filter(Company.id == company_id).first()
    db_company.is_active = False
    db.commit()
    db.refresh(db_company)
    return True


def get_user_by_id(user_id: int, db: Session):
    data = db.query(User).filter(User.id == user_id).first()
    if data.is_active == False:
        return None
    else:
        return data
    
def get_user_by_company_id(company_id: int, db: Session):
    data = db.query(User).filter(User.company_id == company_id, User.is_active != False).all()
    return data

# def get_all_users(db: Session):
#     users = db.query(User).all()
#     for user in users:
#         if user.is_active == False:
#             users.remove(user)
#     return UserOut(id=user.id, username=user.username, company_name=user.company.company_name)

def get_all_users(db: Session):
    users = db.query(User).filter(User.is_active == True).options(joinedload(User.subscription_counts)).all()  # Fetch only active users
    return [
        UserOut(
            id=user.id,
            username=user.username,
            company_name=user.company.company_name if user.company else None,  # Handle None
            hit_count=(sorted(user.subscription_counts, key=lambda x: (x.year, x.month), reverse=True)[0].request_count
            if user.subscription_counts else 0)  # Get the latest count
        )
        for user in users
    ]

def update_user(user_id: int, username: str, password: str, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if username is not None:
        user.username = username
    if password is not None:
        user.hashed_password = get_password_hash(password)
    db.commit()
    db.refresh(user)
    return user


def get_company_header_data(db: Session):
    total_company = db.query(Company).filter(Company.is_active == True).count()
    total_hit_count = db.query(func.sum(Subscription.total_count)).scalar() 
    return {
        "total_company": total_company,
        "total_hit_count": total_hit_count
    }
    
    
def get_user_header_data(db: Session):
    total_user = db.query(User).filter(User.is_active == True).count()
    total_hit_count = db.query(func.sum(UserSubscriptionCount.request_count)).scalar() 
    total_hit_count = total_hit_count if total_hit_count is not None else 0
    return {
        "total_user": total_user,
        "total_hit_count": total_hit_count
    }
    

def get_company_homepage_data(db: Session, user: User):
    
    company = db.query(Subscription).filter(Subscription.company_id == user.company_id).first()
    
    if company and company.plan and company.plan.max_request is not None:
        remaining_hits = company.plan.max_request - company.total_count
        total_additional_hits = abs(remaining_hits) if remaining_hits < 0 else 0
    else:
        total_additional_hits = 0
        
    employee_count = db.query(User).filter(User.company_id == user.company_id).count()
    
    assigned_limit_of_hits = company.plan.max_request if company and company.plan else 0
    used_hits = company.total_count if company else 0
    
    balance_hits = assigned_limit_of_hits - used_hits if company else 0
    if balance_hits < 0:
        balance_hits = 0
        
    price_per_request = company.plan.additional_price_per_request if company and company.plan else 0
    
    total_amount = total_additional_hits * price_per_request if company and company.plan else 0
    if total_amount < 0:
        total_amount = 0
        
    return {
        "total_additional_hits": total_additional_hits,
        "employee_count": employee_count,
        "assigned_limit_of_hits": assigned_limit_of_hits,
        "used_hits": used_hits,
        "balance_hits": balance_hits,
        "price_per_request": price_per_request,
        "total_amount": total_amount
    }
    