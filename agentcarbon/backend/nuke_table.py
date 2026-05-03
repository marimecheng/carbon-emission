from sqlalchemy import text
from app.database import SessionLocal

def drop_emissions_table():
    print("WARNING: Dropping table 'public.emissions' to apply schema changes...")
    db = SessionLocal()
    try:
        # We need to drop it with CASCADE because it might have deps, and we want to recreate it clean
        db.execute(text("DROP TABLE IF EXISTS public.emissions CASCADE"))
        db.commit()
        print("Table 'public.emissions' dropped successfully.")
        print("Restart Uvicorn to have it recreated automatically by SQLAlchemy.")
    except Exception as e:
        print(f"Error dropping table: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    drop_emissions_table()
