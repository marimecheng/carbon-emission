from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt
import os
from .database import get_db
from .models import User

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "openthepodbaydoorshal")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create schema for user
    schema_name = f"user_{new_user.id}"
    try:
        db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        db.commit()
        
        # Create tables in the new schema
        # We need a new connection or to switch the current one's search path
        # Using db.bind (engine) to connect and execute creation
        from .database import engine, Base
        with engine.connect() as connection:
            connection.execute(text(f"SET search_path TO {schema_name}"))
            connection.commit() # Ensure search_path is set for the transaction if needed, though usually per-session
            
            # Create tables that are NOT in public schema (i.e. Emission)
            # Base.metadata.create_all checks the bind. 
            # We must bind the engine/connection with the search path handling.
            # Simpler approach: Create specific tables.
            from .models import Emission
            Emission.__table__.create(bind=connection)
            
    except Exception as e:
        print(f"Error creating schema or tables: {e}")
        # Consider rolling back user creation if schema creation fails
    
    access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(db_user.id), "email": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}
