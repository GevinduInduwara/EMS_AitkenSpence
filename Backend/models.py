from sqlalchemy import Column, Integer, String, DateTime, JSON
from database import Base
from typing import List, Optional
from pydantic import BaseModel

# Database Models
class DBUser(Base):
    __tablename__ = "users"

    emp_no = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    rank = Column(String(50))
    tel = Column(Integer)
    site_name = Column(String(100))
    security_firm = Column(String(100))
    hashed_password = Column(String(255))
    role = Column(String(20))
    managed_employees = Column(JSON)  # Storing list as JSON

# Pydantic Models
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    emp_no: int
    name: str
    rank: str
    tel: int
    site_name: str
    security_firm: str

class UserCreate(UserBase):
    password: str
    role: str
    managed_employees: List[int]

class User(UserBase):
    role: str
    managed_employees: List[int]
    
    class Config:
        from_attributes = True  # Replaces orm_mode = True in Pydantic v2

class UserInDB(User):
    hashed_password: str

class EmployeeProfile(BaseModel):
    emp_no: int
    name: str
    rank: str
    tel: int
    site_name: str
    security_firm: str

class AttendanceRecord(BaseModel):
    emp_no: int
    timestamp: DateTime
    type: str
    recorded_by: int