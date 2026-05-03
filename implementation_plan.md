# Implementation Plan - AgentCarbon SaaS Upgrade

## Status: Completed (Backend + Frontend)

I have successfully upgraded both the Backend and Frontend of AgentCarbon to support multi-tenant SaaS architecture.

---

## 1. Backend Upgrade (Completed)
- **Multi-Tenancy**:
  - **Schema Isolation**: Using Postgres schemas (`user_{id}`) to isolate tenant data.
  - **Auto-Provisioning**: The `POST /auth/register` endpoint now creates a user, a new schema, and initializes required tables (`emissions`) in that schema.
  - **Context-Aware Database**: `get_current_user` dependency automatically switches the DB session's `search_path` to the user's schema.
- **Authentication**:
  - Implemented JWT logic using `python-jose` and `passlib`.
  - Added email to JWT payload for frontend display.
- **Hybrid RAG**:
  - Integrated **Neo4j** (Knowledge Graph) and **Qdrant** (Vector).
  - Ensured data stored in RAG is tagged with `user_id`.

## 2. Frontend Upgrade (Completed)
- **Authentication Infrastructure**:
  - **Axios Interceptor** (`src/api/axios.ts`): Automatically attaches `Authorization: Bearer <token>` to requests and handles 401 redirects.
  - **Auth Context** (`src/context/AuthContext.tsx`): Manages global user state and decodes JWT to get user email.
- **User Interface**:
  - **Login / Register**: Created clean, responsive pages in specific routes.
  - **Dashboard**: Protected the main dashboard behind a `ProtectedRoute` wrapper.
  - **Header**: Added user email display and a Logout button.
- **Integration**:
  - **UploadCard**: Updated to use the secure `api` instance instead of fetch, ensuring uploads are attached to the logged-in user.

---

## Instructions to Run

### 1. Backend
Ensure your `.env` is set up with Database, Neo4j, and Qdrant credentials.
```bash
cd final_year_project
# Install requirements if not done: pip install -r agentcarbon/backend/requirements.txt
uvicorn agentcarbon.backend.app.main:app --reload
```

### 2. Frontend
Navigate to the frontend directory:
```bash
cd agentcarbon/frontend/carbon-footprint-insights
# Install dependencies if not done
npm install axios react-router-dom jwt-decode
# Run the dev server
npm run dev
```

You can now visit the frontend URL (usually `http://localhost:5173`), register a new user, and experience the full isolated SaaS flow!
