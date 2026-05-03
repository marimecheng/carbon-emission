
# Task: Upgrade AgentCarbon to Multi-Tenant SaaS with Hybrid RAG

## Context
I am upgrading my sustainability app, **AgentCarbon**, from a prototype to a multi-tenant enterprise app. 
- **Tech Stack:** FastAPI (Backend), Postgres (User Data), Qdrant (Vector DB), Neo4j (Knowledge Graph).
- **Constraint:** **DO NOT USE LANGCHAIN.** Use native libraries: `qdrant-client`, `neo4j` driver, and `sqlalchemy`.

## Objective
Implement JWT Authentication, Multi-tenant Postgres isolation (Schema-per-user), and a Hybrid Retrieval system (Vector + Graph) where all data is isolated by `user_id`.

---

## Phase 1: Authentication & Identity
1. **Security:** Create `backend/app/auth.py`. Use `passlib[bcrypt]` for password hashing and `python-jose[cryptography]` for JWT tokens.
2. **User Model:** Create a `User` table in the `public` schema of Postgres (id, email, hashed_password).
3. **Endpoints:** 
   - `POST /auth/register`: Create user, hash password, and **programmatically create a Postgres schema** named `user_{user_id}`.
   - `POST /auth/login`: Verify credentials and return a JWT containing the `user_id`.
4. **Dependency:** Create a `get_current_user` dependency in `dependencies.py` to protect routes.

## Phase 2: Multi-Tenant Postgres (Schema Isolation)
1. **Schema Switching:** In `database.py`, implement a SQLAlchemy execution listener. When a request comes in, it must run `SET search_path TO user_{user_id}, public;` so that all subsequent queries for that request are isolated to that user's schema.
2. **Migrations:** Ensure that when a new user registers, the `emissions` table structure is mirrored into their new schema.

## Phase 3: Hybrid RAG Refactor (rag.py)
Refactor the existing `rag.py` to support multi-tenancy and Graph relations:
1. **Qdrant (Vector):** 
   - Every `upsert` must include `user_id` in the payload.
   - Every `scroll` or `search` must use a `Filter` (FieldCondition) where `user_id == current_user_id`.
2. **Neo4j (Graph):**
   - Use the native `neo4j` Python driver.
   - When a document is stored, create the following Knowledge Graph structure:
     `(u:User {id: user_id})-[:OWNS]->(f:Facility {name: facility_name})-[:GENERATED]->(b:Bill {id: doc_id, kwh: kwh, co2: co2})`.
3. **Hybrid Logic:** Add a function `get_hybrid_insights(user_id)` that combines semantic data from Qdrant and relational data (total emissions per facility) from Neo4j using native Cypher queries.

## Phase 4: Integration
1. Update `main.py` to protect the `/predict` and `/history` routes.
2. Pass the `user_id` from the `get_current_user` dependency down into the `rag.py` functions.
3. Update `requirements.txt` to include: `python-jose[cryptography]`, `passlib[bcrypt]`, `neo4j`, `psycopg2-binary`.

---

### Final Instructions for AI:
- Ensure all database connections are handled via environment variables (`DATABASE_URL`, `NEO4J_URI`, `QDRANT_URL`).
- Maintain the existing logic for calculating emissions, but ensure the data is saved to both Postgres, Qdrant, and Neo4j simultaneously.
- Provide clean, modular code.

***

