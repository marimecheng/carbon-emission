# AgentCarbon

AgentCarbon is a comprehensive Carbon Footprint Analysis System designed to accurately measure, track, and forecast carbon emissions. 

## Project Structure

This project is divided into two main components:
- **Backend:** A robust API built with Python and FastAPI, handling calculations, AI predictions, and RAG-based explanations.
- **Frontend:** A modern, interactive web application built with React, Vite, and Tailwind CSS.
- **Infrastructure:** Docker Compose setup containing PostgreSQL, Neo4j, and Qdrant.

---

## Getting Started (The Easy Way - Docker)

The recommended way to run the entire AgentCarbon stack is using Docker Compose. This ensures all services (Frontend, Backend, Postgres, Neo4j, and Qdrant) are correctly configured and connected.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Running with Docker

1. **Navigate to the project root directory** (where `docker-compose.yml` is located).

2. **Start the environment:**
   ```bash
   docker compose up -d --build
   ```

3. **Access the Application:**
   - **Frontend UI:** `http://localhost:8080`
   - **Backend API Docs:** `http://localhost:8000/docs`
   - **Neo4j Browser:** `http://localhost:7474` (Default login: `neo4j` / `password`)

4. **View Logs:**
   ```bash
   docker compose logs -f
   ```

5. **Stop the environment:**
   ```bash
   docker compose down
   ```

---

## Local Development Setup (Manual)

If you need to run the services individually for development, you can still use the manual setup. Note that you will still need the database services running. You can start just the datastores via Docker:
```bash
docker compose up -d postgres neo4j qdrant
```

### Running the Backend (FastAPI)

1. **Navigate to the backend directory:**
   ```bash
   cd agentcarbon/backend
   ```

2. **Create and activate a virtual environment (Recommended):**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS / Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

### Running the Frontend (React + Vite)

1. **Navigate to the frontend directory:**
   ```bash
   cd agentcarbon/frontend/carbon-footprint-insights
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   *The local server will start, typically accessible at `http://localhost:5173`.*
