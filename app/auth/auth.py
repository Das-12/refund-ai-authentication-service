from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.auth.request_models import CompanyCreate, UserOut
from .models import Company, User,APIKey
from ..config import settings
import secrets
from sqlalchemy.orm import Session
from app.auth.request_models import UserOut

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
    if user.is_active == False:
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
    data = db.query(Company).all()
    for user in data:
        if user.is_active == False:
            data.remove(user)
    return data


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

# def get_all_users(db: Session):
#     users = db.query(User).all()
#     for user in users:
#         if user.is_active == False:
#             users.remove(user)
#     return UserOut(id=user.id, username=user.username, company_name=user.company.company_name)

def get_all_users(db: Session):
    users = db.query(User).filter(User.is_active == True).all()  # Fetch only active users
    return [
        UserOut(
            id=user.id,
            username=user.username,
            company_name=user.company.company_name if user.company else None  # Handle None
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