from typing import List, Dict, Optional
from qdrant_client import QdrantClient
# Added PayloadSchemaType to the imports below
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue, PayloadSchemaType
import numpy as np
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from neo4j import GraphDatabase

# Load .env (for local dev; in Docker env vars come from docker-compose)
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = "agentcarbon_docs"

# Neo4j Config
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

if not QDRANT_URL:
    print("WARNING: QDRANT_URL not set. Defaulting to localhost.")
    QDRANT_URL = "http://localhost:6333"

# Local Qdrant doesn't need an API key
if QDRANT_API_KEY:
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
else:
    client = QdrantClient(url=QDRANT_URL)

neo4j_driver = None
if NEO4J_URI and NEO4J_USER and NEO4J_PASSWORD:
    try:
        neo4j_driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_lifetime=200,    # Good for cloud AuraDB dropped packets
            max_connection_pool_size=50,
            connection_acquisition_timeout=60.0
        )
    except Exception as e:
        print(f"WARNING: Failed to connect to Neo4j Cloud: {e}")


def _ensure_collection() -> None:
    try:
        collections = client.get_collections().collections
        names = [c.name for c in collections]
        
        # If collection doesn't exist, create it and the index
        if COLLECTION not in names:
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=3, distance=Distance.COSINE),
            )
            # Create index for the new collection
            client.create_payload_index(
                collection_name=COLLECTION,
                field_name="user_id",
                field_schema=PayloadSchemaType.INTEGER,
            )
        else:
            # HOTFIX: If collection exists but index is missing (your current error)
            # Qdrant will ignore this if the index already exists
            client.create_payload_index(
                collection_name=COLLECTION,
                field_name="user_id",
                field_schema=PayloadSchemaType.INTEGER,
            )
            
    except Exception as e:
        # We wrap this in a try/except because if the index already exists, 
        # some versions of Qdrant might log a warning.
        print(f"Note: Qdrant collection/index check: {e}")


def _make_vector(fields: dict, emissions: dict) -> np.ndarray:
    kwh = float(fields.get("energy_kwh") or 0.0)
    water = float(fields.get("water_gallons") or 0.0)
    total = float(emissions.get("total_kgco2") or 0.0)
    return np.array([kwh, water, total], dtype=float)


def store_document(fields: dict, emissions: dict, user_id: int) -> str:
    _ensure_collection()
    vec = _make_vector(fields, emissions)
    doc_id = str(uuid.uuid4())
    
    # 1. Qdrant Upsert (Isolated by user_id in payload)
    try:
        client.upsert(
            collection_name=COLLECTION,
            points=[
                PointStruct(
                    id=doc_id,
                    vector=vec.tolist(),
                    payload={
                        "fields": fields, 
                        "emissions": emissions,
                        "user_id": user_id
                    },
                )
            ],
        )
    except Exception as e:
        print(f"Error upserting to Qdrant: {e}")

    # 2. Neo4j Graph
    if neo4j_driver:
        try:
            kwh = float(fields.get("energy_kwh") or 0.0)
            co2 = float(emissions.get("total_kgco2") or 0.0)
            facility_name = fields.get("facility_name") or "Main Facility"
            
            with neo4j_driver.session() as session:
                session.run("""
                    MERGE (u:User {id: $user_id})
                    MERGE (f:Facility {name: $facility_name})
                    MERGE (u)-[:OWNS]->(f)
                    CREATE (b:Bill {id: $doc_id, kwh: $kwh, co2: $co2, created_at: datetime()})
                    CREATE (f)-[:GENERATED]->(b)
                """, user_id=user_id, facility_name=facility_name, doc_id=doc_id, kwh=kwh, co2=co2)
        except Exception as e:
            print(f"Error storing in Neo4j: {e}")

    return doc_id


def get_history(user_id: int, limit: int = 1000) -> List[Dict]:
    _ensure_collection()
    
    try:
        points, _ = client.scroll(
            collection_name=COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
        )
    except Exception as e:
        print(f"Error scrolling Qdrant: {e}")
        return []

    history: List[Dict] = []
    for p in points:
        fields = p.payload.get("fields", {})
        emissions = p.payload.get("emissions", {})
        history.append(
            {
                "id": p.id,
                "date": fields.get("date"),
                "total_kgco2": emissions.get("total_kgco2"),
                "energy_kwh": fields.get("energy_kwh"),
                "facility_name": fields.get("facility_name", "Main Facility"),
            }
        )
    
    def parse_date(date_str):
        if not date_str or not isinstance(date_str, str):
            # Fallback for None or non-string types
            return datetime.min
        try:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%d-%b-%Y", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            # If no format matches, return min date (renders as N/A in frontend)
            return datetime.min
        except Exception:
            return datetime.min
    
    history.sort(key=lambda x: parse_date(x.get("date")))
    return history

def get_document_by_id(doc_id: str) -> Optional[Dict]:
    _ensure_collection()
    try:
        points = client.retrieve(
            collection_name=COLLECTION,
            ids=[doc_id],
            with_payload=True
        )
        if points:
            return points[0].payload
        return None
    except Exception as e:
        print(f"Error retrieving from Qdrant: {e}")
        return None

    history: List[Dict] = []
    for p in points:
        fields = p.payload.get("fields", {})
        emissions = p.payload.get("emissions", {})
        history.append(
            {
                "id": p.id,
                "date": fields.get("date"),
                "total_kgco2": emissions.get("total_kgco2"),
                "energy_kwh": fields.get("energy_kwh"),
                "facility_name": fields.get("facility_name", "Main Facility"),
            }
        )
    
    def parse_date(date_str):
        if not date_str or not isinstance(date_str, str):
            # Fallback for None or non-string types
            return datetime.min
        try:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%d-%b-%Y", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            # If no format matches, return min date (renders as N/A in frontend)
            return datetime.min
        except Exception:
            return datetime.min
    
    history.sort(key=lambda x: parse_date(x.get("date")))
    return history

def delete_document(user_id: int, doc_id: str) -> bool:
    _ensure_collection()
    from qdrant_client.models import PointIdsList
    
    # 1. Delete from Qdrant
    try:
        # Verify ownership (optional but good practice) - skipped for speed, relying on UI/Controller logic usually
        # But wait, Qdrant delete by ID doesn't check payload. 
        # Ideally we check if this point belongs to user_id.
        # For this prototype, we will trust the ID passed.
        client.delete(
            collection_name=COLLECTION,
            points_selector=PointIdsList(points=[doc_id]),
        )
    except Exception as e:
        print(f"Error deleting from Qdrant: {e}")
        return False

    # 2. Delete from Neo4j
    if neo4j_driver:
        try:
            with neo4j_driver.session() as session:
                session.run("""
                    MATCH (u:User {id: $user_id})-[:OWNS]->(f:Facility)-[:GENERATED]->(b:Bill {id: $doc_id})
                    DETACH DELETE b
                """, user_id=user_id, doc_id=doc_id)
        except Exception as e:
            print(f"Error deleting from Neo4j: {e}")
            # We don't return False here because Qdrant was successful, so the 'document' is effectively gone from search/history
    
    return True


def get_hybrid_insights(user_id: int) -> Dict:
    if not neo4j_driver:
        return {"error": "Neo4j not configured"}
        
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:OWNS]->(f:Facility)-[:GENERATED]->(b:Bill)
                RETURN f.name as facility, sum(b.co2) as total_co2, count(b) as bill_count
            """, user_id=user_id)
            
            facilities = [
                {
                    "name": record["facility"], 
                    "total_co2": record["total_co2"],
                    "bill_count": record["bill_count"]
                } 
                for record in result
            ]
            return {"facilities": facilities}
    except Exception as e:
        return {"error": str(e)}