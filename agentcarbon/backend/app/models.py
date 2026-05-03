from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Emission(Base):
    __tablename__ = "emissions"
    # No schema arg -> defaults to current search_path

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    facility_name = Column(String, index=True)
    date = Column(String)
    energy_kwh = Column(Float)
    water_gallons = Column(Float)
    total_kgco2 = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
