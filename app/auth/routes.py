from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.kafka_producer import send_log
from .auth import authenticate_user, create_access_token, create_user, get_user, decode_access_token,get_api_key,create_api_key
from ..database import get_db
from .models import ApiRequest, UserCreate

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/apikeys")
async def create_api_key_for_user(token: str = Depends(oauth2_scheme), expiry_minutes: int = 60, db: Session = Depends(get_db)):
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user(db, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    api_key = create_api_key(db, user, expiry_minutes)
    return {"api_key": api_key.key, "expires_at": api_key.expires_at}

@router.get("/apikeys")
async def list_api_keys_for_user(token: str = Depends(oauth2_scheme),  db: Session = Depends(get_db)):
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user(db, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"api_keys": [api.key for api in user.api_keys]}

@router.post("/validate-key")
async def validate_api_key(api_request: ApiRequest, db: Session = Depends(get_db)):
    key = get_api_key(db, api_request.api_key)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return {"valid": True, "user": key.owner.username}

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    log_data = {
            "method": "POST",
            "url": "/token",
            "user_agent": "Chrome",
            "ip_address": "127.0.0.1",
            "token": "access_token",
            "request_body": "form_data",
            "response_body": {"access_token": access_token, "token_type": "bearer"},
            "status_code": 200,
        }
    send_log( log_data)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    new_user = create_user(db, user.username, user.password)
    return {"username": new_user.username}


@router.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"username": user.username}
