import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# from app.kafka_producer import send_count
from app.permissions.models import Role
from app.permissions.permissions import has_permission
from .auth import (authenticate_user, create_access_token, create_company, create_user, get_company, get_company_with_apikey, get_user,
                   decode_access_token,get_api_key,create_api_key, is_api_key_valid, get_all_company, get_company_by_id, update_company,
                   update_user, delete_company, get_user_by_id, get_all_users, get_user_by_company_id,get_company_header_data,get_user_header_data,
                   get_company_homepage_data)
from ..database import get_db
from .request_models import ApiRequest, CompanyCreate, LoginRequest, TokenVerificationRequest, UserCreate, TokenRequest, UpdateCompany, UserOut, UserUpdate
import logging
from typing import List


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/token/refresh")
async def refresh_token( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        login_user = get_user(db, username=decode_access_token(token))
        if not login_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(data={"sub": login_user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logging.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/login")
async def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        logging.error(f"Error logging in: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/register/user",status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate,token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print("register user started")
    try:
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user not found",
            )
        db_user = get_user(db, user.username)
            
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        if has_permission(login_user, "create_user"):
            new_user = create_user(db, user.username, user.password)
            new_user.company_id = user.company_id
            db.commit()
            db.refresh(new_user)
            staff_role = db.query(Role).filter(Role.name == "staff").first()
            if staff_role not in new_user.roles:
                new_user.roles.append(staff_role)
                db.commit()
                db.refresh(new_user)
            return {"username": new_user.username}
        elif has_permission(login_user, "create_user_under_company"):
            new_user = create_user(db, user.username, user.password)
            new_user.company = login_user.company
            db.commit()
            db.refresh(new_user)
            staff_role = db.query(Role).filter(Role.name == "staff").first()
            if staff_role not in new_user.roles:
                new_user.roles.append(staff_role)
                db.commit()
                db.refresh(new_user)
            return {"username": new_user.username}
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
    except Exception as e:
        logging.error(f"Error registering user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/register/company",status_code=status.HTTP_201_CREATED)
async def register(company: CompanyCreate,token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        logging.info(f"this is company data {company}")
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

        return {"status":True,"message":"Company Created Successfully","company_id":new_company.id}
    except Exception as e:
        logging.error(f"Error registering company: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        logging.error(f"Error reading user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/verify-token")
async def verify_token(token_request: TokenVerificationRequest, db: Session = Depends(get_db)):
    try:
        token_data = decode_access_token(token_request.token)
        print(f"token data is {token_data}")
        if token_data is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user = get_user(db, username=token_data)
        print(f"user is {user}")
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        print(f"this is user role {[role.name for role in user.roles]}")
        if "super_admin" not in [role.name for role in user.roles]:
            company = get_company_with_apikey(db, token_request.api_key)
            if company.id != user.company.id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key Expired or Invalid")
        print("end of the verify token")
        return {"username": user.username, "role": user.roles[0].name}
    except Exception as e:
        logging.error(f"Error verifying token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/get_company")
async def get_all_company_endpoint(token_request: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        username = decode_access_token(token_request)
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
        if not has_permission(user, "view_company"):

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        companies = get_all_company(db)
        return companies
    except Exception as e:
        logging.error(f"Error getting all companies: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/get_company/{company_id}")
async def get_company_endpoint(company_id: int, token_request: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        username = decode_access_token(token_request)
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
        if not has_permission(user, "view_company"):

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        companies = get_company_by_id(company_id, db)
        return companies
    except Exception as e:
        logging.error(f"Error getting all companies: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/update_company/{company_id}")
async def update_company_endpoint(company_id: int, company: UpdateCompany,token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        logging.info(f"endpoint started working")
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
        if not has_permission(user, "update_company"):

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        company_obj = update_company(company_id,company,db)
        return {"status":True,"message":"Company updated Successfully","updated_company": company_obj}
    except Exception as e:
        logging.error(f"Error updating company: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/delete_company/{company_id}")
async def delete_company_endpoint(company_id: int,token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
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
        if not has_permission(user, "delete_company"):

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        company_obj = delete_company(company_id,db)
        if company_obj:
            return {"status":True,"message":"Company Deleted Successfully"}  
        else:
            return {"status":False,"message":"Company Not Found"}  
    except Exception as e:
        logging.error(f"Error deleting company: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    

@router.get("/get_user/{user_id}", response_model=UserOut)
async def get_user_endpoint(user_id: int,token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        username = decode_access_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request_user = get_user(db, username)
        if request_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if has_permission(request_user, "view_user"):
            user_obj = get_user_by_id(user_id, db)
            return user_obj
        elif has_permission(request_user, "get_users_under_company"):
            user_obj = get_user_by_id(user_id, db)
            if request_user.company_id == user_obj.company_id:
                return user_obj
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="you can only view the user under your company",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
    except Exception as e:
        logging.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    

@router.get("/get_user_by_company_id/{company_id}", response_model=List[UserOut])
async def get_staff_endpoint(company_id: int,token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        username = decode_access_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request_user = get_user(db, username)
        if request_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if has_permission(request_user, "get_users_under_company"):
            user_obj = get_user_by_company_id(company_id, db)
            return user_obj
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
    except Exception as e:
        logging.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/get_all_user", response_model=List[UserOut])
async def get_all_user_endpoint(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        username = decode_access_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_obj = get_user(db, username)
        if user_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if has_permission(user_obj, "view_user"):
            users = get_all_users(db)
            for user in users:
                if user.id == user_obj.id:
                    users.remove(user)
            return users
        elif has_permission(user_obj, "get_users_under_company"):
            users = get_all_users(db)
            users_list = []
            for user in users:
                if user.company_id == user_obj.company_id and user.id != user_obj.id:
                    users_list.append(user)
            logging.info(f"this is all users {users_list}")
            return users_list
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    except Exception as e:
        logging.error(f"Error getting all users: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.put("/update_user/{user_id}", response_model=UserOut)
async def update_user_endpoint(user_id: int, user: UserUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        username = decode_access_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request_user = get_user(db, username)
        if request_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if has_permission(request_user, "update_user"):
            user_obj = update_user(user_id, user.username, user.password, db)
            return user_obj
        elif has_permission(request_user, "update_user_under_company"):
            user_obj = get_user_by_id(user_id, db)
            if request_user.company_id == user_obj.company_id:
                user_obj = update_user(user_id, user.username, user.password, db)
                return user_obj
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="you can only update the user under your company",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    except Exception as e:
        logging.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
@router.delete("/delete_user/{user_id}")
async def delete_user_endpoint(user_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        username = decode_access_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request_user = get_user(db, username)
        if request_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if has_permission(request_user, "delete_user"):
            user_obj = get_user_by_id(user_id, db)
            user_obj.is_active = False
            db.commit()
            db.refresh(user_obj)
            return {"status":True,"message":"User Deleted Successfully"}
        elif has_permission(request_user, "delete_user_under_company"):
            user_obj = get_user_by_id(user_id, db)
            if request_user.company_id == user_obj.company_id:
                user_obj.is_active = False
                db.commit()
                db.refresh(user_obj)
                return {"status":True,"message":"User Deleted Successfully"}
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="you can only delete the user under your company",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    except Exception as e:
        logging.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
    
@router.get("/header_api_company")
async def header_api_company(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print("header api company in auth started")
    
    try:
        username = decode_access_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request_user = get_user(db, username)
        if request_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        header_data = get_company_header_data(db)
        return header_data
    except Exception as e:
        logging.error(f"Error getting company header data: {str(e)}")
        
        
        
@router.get("/header_api_user")
async def header_api_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print("header api user in auth started")
    
    try:
        username = decode_access_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request_user = get_user(db, username)
        if request_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        header_data = get_user_header_data(db)
        return header_data
    except Exception as e:
        logging.error(f"Error getting user header data: {str(e)}")
        
        
@router.get("/get_company_homepage_data")
async def get_company_homepage_data_auth(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # print("get company homepage data started")
    try:
        username = decode_access_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request_user = get_user(db, username)
        if request_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        header_data = get_company_homepage_data(db, request_user)
        return header_data
    except Exception as e:
        logging.error(f"Error getting company homepage data: {str(e)}")