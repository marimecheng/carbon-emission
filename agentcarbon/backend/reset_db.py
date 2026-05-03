import os
from sqlalchemy import text
from app.database import SessionLocal
from app.models import User
from app.rag import client, COLLECTION, neo4j_driver
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType

def reset_all_data():
    print("WARNING: This will delete ALL upload data (Emissions, History, Knowledge Graph) for ALL users.")
    print("User accounts (login credentials) will be PRESERVED.")
    confirm = input("Type 'DELETE' to confirm: ")
    if confirm != "DELETE":
        print("Aborted.")
        return

    db = SessionLocal()
    try:
        # 1. Postgres: Clear Emissions for all users
        print("Scaning users...")
        users = db.query(User).all()
        for user in users:
            schema = f"user_{user.id}"
            print(f"Cleaning schema: {schema}...")
            try:
                # Check if schema exists/is accessible by trying to set path
                db.execute(text(f"SET search_path TO {schema}, public"))
                # Truncate emissions table
                # We use raw SQL because Emission model binds to current search path
                # 'TRUNCATE TABLE emissions' works if the table exists in that schema
                db.execute(text("TRUNCATE TABLE emissions RESTART IDENTITY CASCADE"))
                db.commit()
            except Exception as e:
                print(f"  Skipping {schema} (might not exist or empty): {e}")
                db.rollback()

        # 2. Qdrant: Recreate Collection
        print("Resetting Qdrant Collection...")
        try:
            client.delete_collection(COLLECTION)
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=3, distance=Distance.COSINE),
            )
            client.create_payload_index(
                collection_name=COLLECTION,
                field_name="user_id",
                field_schema=PayloadSchemaType.INTEGER,
            )
            print("Qdrant reset successful.")
        except Exception as e:
            print(f"Qdrant error: {e}")

        # 3. Neo4j: Detach Delete All
        if neo4j_driver:
            print("Resetting Neo4j Graph...")
            try:
                with neo4j_driver.session() as session:
                    session.run("MATCH (n) DETACH DELETE n")
                print("Neo4j reset successful.")
            except Exception as e:
                print(f"Neo4j error: {e}")
        else:
            print("Neo4j driver not available, skipping.")

        print("\n=== SYSTEM RESET COMPLETE ===")
        print("All user data has been wiped. User accounts remain active.")

    finally:
        db.close()

if __name__ == "__main__":
    reset_all_data()
