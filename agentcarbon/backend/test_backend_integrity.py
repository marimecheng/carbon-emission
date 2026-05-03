import os
import sys
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time

# Configuration
BASE_URL = "http://localhost:8000"
DATABASE_URL = "postgresql://postgres:password@localhost:5432/agentcarbon"

# Unique user
random_suffix = int(time.time())
TEST_EMAIL = f"test_user_{random_suffix}@example.com"
TEST_PASS = "securepassword123"
TEST_USER = {
    "email": TEST_EMAIL,
    "password": TEST_PASS
}

def check_backend_integrity():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    print("1. Checking Database Connection...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   [PASS] Connected to Postgres.")
    except Exception as e:
        print(f"   [FAIL] Could not connect to DB: {e}")
        return False

    print("\n2. Testing Registration (Schema Isolation)...")
    reg_url = f"{BASE_URL}/auth/register"
    try:
        resp = requests.post(reg_url, json=TEST_USER)
        if resp.status_code != 200:
            print(f"   [FAIL] Registration failed: {resp.text}")
            return False
        print("   [PASS] Registration HTTP 200.")
    except Exception as e:
        print(f"   [FAIL] Request error: {e}")
        return False
        
    # Verify User and Schema in DB
    try:
        # Get User ID
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": TEST_EMAIL})
        user_row = result.fetchone()
        if not user_row:
            print("   [FAIL] User not found in DB users table.")
            return False
        user_id = user_row[0]
        print(f"   [PASS] User found in DB ID: {user_id}")
        
        # Check Schema
        schema_name = f"user_{user_id}"
        schema_check = db.execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'"))
        if schema_check.fetchone():
            print(f"   [PASS] Schema '{schema_name}' created successfully.")
        else:
            print(f"   [FAIL] Schema '{schema_name}' was NOT created.")
            return False
            
    except Exception as e:
        print(f"   [FAIL] Error verifying DB state: {e}")
        return False
    finally:
        db.close()

    print("\n3. Testing Login...")
    login_url = f"{BASE_URL}/auth/login"
    try:
        resp = requests.post(login_url, json=TEST_USER)
        if resp.status_code == 200:
            print("   [PASS] Login HTTP 200. Token received.")
        else:
            print(f"   [FAIL] Login failed: {resp.text}")
            return False
    except Exception as e:
        print(f"   [FAIL] Request error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = check_backend_integrity()
    if success:
        print("\nAll Systems Operational.")
        sys.exit(0)
    else:
        print("\nSystem Check Failed.")
        sys.exit(1)
