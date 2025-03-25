from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from database import Base

# Database Models
class DBUser(Base):
    __tablename__ = "users"

    emp_no = Column(String(20), primary_key=True, index=True)
    name = Column(String(100))
    rank = Column(String(50))
    tel = Column(String(20))
    site_name = Column(String(100))
    security_firm = Column(String(100))
    hashed_password = Column(String(255))
    role = Column(String(20))
    managed_employees = Column(JSON)

class DBAttendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    emp_no = Column(String(20), ForeignKey('users.emp_no'))
    timestamp = Column(DateTime)
    type = Column(String(10))  # "in" or "out"
    recorded_by = Column(String(20), ForeignKey('users.emp_no'))

# Pydantic Models/Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    emp_no: str
    name: str
    rank: str
    tel: str
    site_name: str
    security_firm: str
    role: str
    managed_employees: List[str]

    class Config:
        orm_mode = True

class UserInDB(User):
    hashed_password: str

class EmployeeProfile(BaseModel):
    emp_no: str
    name: str
    rank: str
    tel: str
    site_name: str
    security_firm: str

class AttendanceRecord(BaseModel):
    emp_no: str
    timestamp: datetime
    type: str
    recorded_by: str