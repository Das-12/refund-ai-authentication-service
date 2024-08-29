from typing import Optional
from pydantic import BaseModel

class CompanyCreate(BaseModel):
    username: str
    password: str
    company_name: str
    contact_person_name: str
    email: str
    phone_number: str
    secondary_phone_number: str
    api_keys: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

class ApiRequest(BaseModel):
    api_key: str

class TokenVerificationRequest(BaseModel):
    token: str
    api_key: str
