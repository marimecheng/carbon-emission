from sqlalchemy import text
from app.database import SessionLocal
from app.models import User, Emission

def print_all_data():
    db = SessionLocal()
    try:
        print("=== USERS ===")
        users = db.query(User).all()
        if not users:
            print("No users found.")
        
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}")
        
        print("\n=== DATA PER USER ===")
        for user in users:
            print(f"\n--- Data for User: {user.email} (ID: {user.id}) ---")
            schema = f"user_{user.id}"
            try:
                # Switch schema
                db.execute(text(f"SET search_path TO {schema}, public"))
                
                # Query emissions in this schema
                emissions = db.query(Emission).all()
                if not emissions:
                    print("  No emissions records found.")
                else:
                    for e in emissions:
                        print(f"  - ID: {e.id} | Date: {e.date} | Facility: {e.facility_name} | CO2: {e.total_kgco2} kg | Energy: {e.energy_kwh} kWh")
            except Exception as e:
                print(f"  Error accessing schema {schema}: {e}")
                db.rollback()

    finally:
        db.close()

if __name__ == "__main__":
    print_all_data()
