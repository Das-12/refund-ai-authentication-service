import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.kafka_producer import send_count
from app.permissions.models import Role
from app.permissions.permissions import has_permission
from .auth import authenticate_user, create_access_token, create_company, create_user, get_company, get_company_with_apikey, get_user, decode_access_token,get_api_key,create_api_key, is_api_key_valid
from ..database import get_db
from .request_models import ApiRequest, CompanyCreate, LoginRequest, TokenVerificationRequest, UserCreate

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/token/refresh")
async def refresh_token( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    login_user = get_user(db, username=decode_access_token(token))
    if not login_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": login_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login")
async def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    isSuperAdmin = False
    for role in user.roles:
        if role.name=='super_admin':
            isSuperAdmin = True
            break

    if isSuperAdmin:
        return {"access_token": access_token, "token_type": "bearer"}
    
    return {"access_token": access_token, "token_type": "bearer","api_key":user.company.api_keys.key}

@router.post("/register/user",status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate,token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username=decode_access_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    login_user = get_user(db, username)
    if login_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not has_permission(login_user, "create_user_under_company"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    db_user = get_user(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    new_user = create_user(db, user.username, user.password)
    
    new_user.company = login_user.company
    db.commit()
    db.refresh(new_user)
    staff_role = db.query(Role).filter(Role.name == "company").first()
    if staff_role not in new_user.roles:
        new_user.roles.append(staff_role)
        db.commit()
        db.refresh(new_user)
    
    return {"username": new_user.username}

@router.post("/register/company",status_code=status.HTTP_201_CREATED)
async def register(company: CompanyCreate,token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, username=decode_access_token(token))
    if not has_permission(user, "create_company"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    db_user = get_user(db, company.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    db_company = get_company(db,company.phone_number)
    if db_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company phone already registered",
        )
    new_company = create_company(db=db,company=company)
    
    new_user = create_user(db, company.username, company.password)
    new_user.company = new_company
    company_role = db.query(Role).filter(Role.name == "company").first()
    if company_role not in new_user.roles:
        new_user.roles.append(company_role)
        db.commit()
        db.refresh(new_user)

    return {"status":True,"message":"Company Created Successfully"}

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

@router.post("/verify-token")
async def verify_token(token_request: TokenVerificationRequest, db: Session = Depends(get_db)):
    token_data = decode_access_token(token_request.token)
    if token_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = get_user(db, username=token_data)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    company = get_company_with_apikey(db,token_request.api_key)
    if company.id != user.company.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key Expired or Invalid")
    
    log_data = {
            'from_url':token_request.from_url,
            'company': company.id,
            'api_key': token_request.api_key,
            'user': user.id,
            'created_on': datetime.utcnow().strftime("%d/%m/%y %H:%M:%S"),
    }
    asyncio.create_task(send_count(log_data))
    
    return {"username": user.username}