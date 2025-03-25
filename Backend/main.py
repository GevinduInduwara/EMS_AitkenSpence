from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
import os
from models import User, UserInDB, Token, TokenData, EmployeeProfile, AttendanceRecord
from database import get_db, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper Functions
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def get_user(db: Session, emp_no: str):
    return db.query(DBUser).filter(DBUser.emp_no == emp_no).first()

def authenticate_user(db: Session, emp_no: str, password: str):
    user = get_user(db, emp_no)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        emp_no: str = payload.get("sub")
        if emp_no is None:
            raise credentials_exception
        token_data = TokenData(username=emp_no)
    except JWTError:
        raise credentials_exception
    
    user = get_user(db, emp_no=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_oic(current_user: User = Depends(get_current_user)):
    if current_user.role != "OIC":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OIC can access this functionality"
        )
    return current_user

# Initialize test data
def initialize_test_data():
    db = SessionLocal()
    try:
        if not db.query(DBUser).filter(DBUser.emp_no == "11138").first():
            test_oic = DBUser(
                emp_no="11138",
                name="M.A.G.I Malwaththa",
                rank="OIC",
                tel="+94 123456789",
                site_name="Aitken Spence HQ",
                security_firm="Oracle",
                hashed_password=get_password_hash("testpassword"),
                role="OIC",
                managed_employees=["11139", "11140"]
            )
            db.add(test_oic)
            
            test_employee1 = DBUser(
                emp_no="11139",
                name="Employee One",
                rank="Security",
                tel="+94 987654321",
                site_name="Aitken Spence HQ",
                security_firm="Oracle",
                hashed_password=get_password_hash("testpassword"),
                role="Employee",
                managed_employees=[]
            )
            db.add(test_employee1)
            
            test_employee2 = DBUser(
                emp_no="11140",
                name="Employee Two",
                rank="Security",
                tel="+94 987654322",
                site_name="Aitken Spence HQ",
                security_firm="Oracle",
                hashed_password=get_password_hash("testpassword"),
                role="Employee",
                managed_employees=[]
            )
            db.add(test_employee2)
            db.commit()
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    try:
        # Test database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Initialize test data
        initialize_test_data()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error during startup: {e}")
        raise

# API Endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.role != "OIC":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OIC can login to the system"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.emp_no}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

# Add all your other endpoints here...
# [Include all your existing endpoints from the original code]