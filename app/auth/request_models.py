from typing import Optional
from pydantic import BaseModel, Field

class CompanyCreate(BaseModel):
    username: str
    password: str
    company_name: str
    contact_person_name: str
    email: str
    phone_number: str
    secondary_phone_number: str
    api_keys: Optional[str] = None
    
class UpdateCompany(BaseModel):
    company_name: Optional[str] = Field(default=None)
    contact_person_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)
    secondary_phone_number: Optional[str] = Field(default=None)
    api_keys: Optional[str] = Field(default=None)

class UserCreate(BaseModel):
    username: str
    password: str
    company_id: Optional[int] = None
    
class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    
class UserOut(BaseModel):
    username: Optional[str] = None
    company_id: Optional[int] = None

class ApiRequest(BaseModel):
    api_key: str

class TokenVerificationRequest(BaseModel):
    token: str
    api_key: Optional[str] = None
    from_url: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenRequest(BaseModel):
    token: str
    
