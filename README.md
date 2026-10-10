# InsightPrep — AI-Powered Interview Preparation & Assessment Platform

InsightPrep is a full-stack, enterprise-grade AI-powered mock interview and performance analysis platform. It provides personalized, adaptive technical and behavioral/HR interviews, real-time speech-to-text input, natural audio question playback, structured answer evaluations (including the STAR methodology for behavioral competencies), and in-depth performance analytics.

---

## Key Features

- **User Authentication & Session Management**: Secure registration, login, and session cookie validation using JWT and argon2/passlib password hashing.
- **Resume Analysis & Custom Tailoring**: PDF and text resume parsing with automated skill extraction, role matching, and interview focus area recommendations.
- **Adaptive Technical Interviews**: Dynamic question generation powered by Large Language Models (LLMs) with Retrieval-Augmented Generation (RAG) context injection from verified computer science knowledge bases (DSA, DBMS, OS, Computer Networks).
- **Behavioral & HR Interviews**: STAR methodology-based interview framework assessing Situation, Task, Action, and Result dimensions, candidate ownership, and decision-making.
- **Speech & Audio Integration**:
  - In-browser real-time speech-to-text (Web Speech API) with live transcription.
  - High-fidelity text-to-speech audio question playback via ElevenLabs API.
- **Multi-Provider AI Fallback Engine**: Production-resilient architecture featuring tiered LLM routing (Google Gemini $\leftrightarrow$ Groq $\leftrightarrow$ deterministic Mock fallback) with automatic retry and timeout handling.
- **In-Depth Performance Analytics**: Multi-dimensional rubrics, category breakdown, actionable feedback, and historical progress tracking.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, Vite, React Router v7, Vanilla CSS / Modern Design System, Web Speech API |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0, Alembic |
| **Database & Vector Search** | PostgreSQL 17 with `pgvector` extension |
| **RAG & Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`), Chunking, Cosine Vector Search |
| **AI / LLM Services** | Google Gemini API (`gemini-3.7-flash`), Groq API (`openai/gpt-oss-120b`), Mock Provider |
| **Audio / Speech** | ElevenLabs Text-to-Speech API, Browser Web Speech Recognition |
| **Code Quality & Testing** | Pytest, Ruff, Black, ESLint |

---

## High-Level Architecture

```
                    ┌────────────────────────────┐
                    │      React Frontend        │
                    │   (Vite / localhost:5173)   │
                    └──────────────┬─────────────┘
                                   │ HTTP / JSON & Audio
                                   ▼
                    ┌────────────────────────────┐
                    │      FastAPI Backend       │
                    │   (Uvicorn / localhost:8000)│
                    └──────┬───────┬───────┬─────┘
                           │       │       │
             ┌─────────────┘       │       └─────────────┐
             ▼                     ▼                     ▼
┌────────────────────────┐  ┌─────────────┐  ┌────────────────────────┐
│ PostgreSQL + pgvector  │  │ LLM Routing │  │ ElevenLabs Audio TTS   │
│  (Docker / port 5433)  │  │  Gemini     │  │ (Question Playback)    │
│  - Users & Resumes     │  │  Groq       │  └────────────────────────┘
│  - Sessions & Reports  │  │  Mock Fallback
│  - 384-dim Embeddings  │  └─────────────┘
└────────────────────────┘
```

---

## Repository Structure

```
LLM-Interview-Preparation/
├── backend/
│   ├── alembic/              # Database schema migrations
│   │   └── versions/         # Migration scripts
│   ├── app/
│   │   ├── api/              # FastAPI route endpoints (auth, interviews, resumes)
│   │   ├── core/             # Configuration, database engine, security & JWT
│   │   ├── models/           # SQLAlchemy ORM models (User, Resume, Interview, Knowledge)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   └── services/         # Business logic, LLM engines, ElevenLabs TTS & RAG
│   │       └── rag/          # Document loader, chunker, embeddings & retrieval
│   ├── tests/                # Automated pytest suite (114 passing tests)
│   ├── alembic.ini           # Alembic migration configuration
│   ├── pyproject.toml        # Backend build configuration
│   ├── requirements.txt      # Python dependencies (UTF-8)
│   └── ruff.toml             # Ruff linter configuration
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components & layouts
│   │   ├── pages/            # View pages (Login, Register, Dashboard, Interview, Results)
│   │   └── styles/           # CSS design system & variables
│   ├── package.json          # Frontend dependencies & scripts
│   └── vite.config.js        # Vite configuration
├── docs/
│   ├── architecture.md       # Detailed technical architecture
│   └── knowledge/            # Computer science domain documents for RAG (DSA, DBMS, OS, CN)
├── docker-compose.yml        # PostgreSQL with pgvector service container
├── .env.example              # Environment variables template
└── README.md                 # Project documentation
```

---

## Prerequisites

Before setting up the project locally, verify that you have installed:

- **Python**: Version `3.12` (recommended). Note: PyTorch & sentence-transformers require Python $\le$ 3.12 on Windows.
- **Node.js**: Version `20.x` or later (with `npm`).
- **Docker Desktop**: Running with Compose enabled.
- **Git**: For version control.

---

## Local Setup & Installation (Windows PowerShell)

### 1. Clone the Repository

```powershell
git clone https://github.com/PJscripts/InsightPrep.git
cd InsightPrep
```

### 2. Configure Environment Variables

Copy the `.env.example` template to `.env` in both the project root and `backend/`:

```powershell
Copy-Item .env.example .env
Copy-Item .env.example backend\.env
```

Edit `backend/.env` to configure your API keys (optional if running in mock fallback mode):
- `DATABASE_URL`: `postgresql+psycopg://interview_user:interview_password@localhost:5433/interview_db`
- `JWT_SECRET`: Enter a secure random string (at least 32 characters).
- `GEMINI_API_KEY`: *(Optional)* Your Google Gemini API key.
- `GROQ_API_KEY`: *(Optional)* Your Groq API key.
- `ELEVENLABS_API_KEY`: *(Optional)* Your ElevenLabs API key for audio playback.

> **Note**: If API keys are omitted, the system automatically falls back to deterministic mock providers, allowing complete offline testing of interviews, evaluations, and reports.

### 3. Start PostgreSQL with pgvector via Docker

InsightPrep requires PostgreSQL with the `pgvector` extension for storing session data and knowledge embeddings:

```powershell
docker compose up -d
```

Verify that the container is healthy and mapped to port `5433`:

```powershell
docker ps
```

### 4. Backend Setup & Alembic Migrations

Open a PowerShell terminal in the `backend/` directory:

```powershell
cd backend

# Create Python 3.12 virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install backend dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run database migrations to initialize all tables:

```powershell
alembic upgrade head
```

#### *(Optional)* Ingest RAG Knowledge Base

To populate the vector database with the computer science curriculum documents (DSA, DBMS, OS, Computer Networks):

```powershell
python -m app.services.rag.ingest_cli --db-url "postgresql+psycopg://interview_user:interview_password@localhost:5433/interview_db"
```

### 5. Start the FastAPI Backend Server

> **Important (Windows Application Control Note)**:
> On some Windows installations, running `.\.venv\Scripts\uvicorn.exe` directly may be restricted by Windows Application Control or AppLocker policies. Launching Uvicorn through the signed Python executable (`python -m uvicorn`) runs reliably without restriction:

```powershell
# From the backend/ directory with .venv active:
python -m uvicorn app.main:app --reload
```

The backend server will run at:
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 6. Frontend Setup & Startup

Open a separate terminal in the `frontend/` directory:

```powershell
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend application will be accessible at:
- Web Application: `http://localhost:5173`

---

## Verifying the Setup & Running Tests

### Backend Unit & Integration Tests

The backend test suite includes 114 automated tests covering authentication, resume parsing, question generation, behavioral STAR evaluation, RAG retrieval, and LLM fallback routing:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

# Run pytest using an in-memory SQLite database for isolated test execution
$env:DATABASE_URL="sqlite:///:memory:"
pytest tests/ -v
```

### Backend Linting & Formatting

```powershell
cd backend
ruff check .
black --check app alembic tests
```

### Frontend Linting & Production Build

```powershell
cd frontend
npm run lint
npm run build
```

---

## Troubleshooting & Known Pitfalls

### 1. `sqlite3.OperationalError: no such table: users`
- **Cause**: PowerShell environment variables take precedence over `.env` files in Pydantic Settings. If `$env:DATABASE_URL="sqlite:///:memory:"` was set during earlier testing in the same terminal session, the FastAPI backend will connect to an empty in-memory SQLite database rather than your PostgreSQL database.
- **Fix**: Clear the shell environment variable in PowerShell:
  ```powershell
  Remove-Item Env:\DATABASE_URL
  ```
  Or verify that `backend/.env` has `DATABASE_URL` pointing to `localhost:5433`.

### 2. Windows Application Control Blocking `uvicorn.exe`
- **Cause**: Windows Application Control policy prevents execution of third-party `.exe` binaries inside virtual environments.
- **Fix**: Always execute Uvicorn as a Python module:
  ```powershell
  python -m uvicorn app.main:app --reload
  ```

### 3. Port Conflict on PostgreSQL (Port 5432 vs 5433)
- If your local machine already runs a native PostgreSQL instance on default port `5432`, the provided `docker-compose.yml` maps container port `5432` to host port `5433`. Ensure your `DATABASE_URL` specifies `localhost:5433`.

---

## API Documentation Overview

Key endpoints provided by the backend (accessible via Swagger at `/docs`):

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/auth/register` | Register a new user account |
| `POST` | `/auth/login` | Authenticate user & set secure HTTP-only cookie |
| `GET` | `/auth/me` | Fetch authenticated user details |
| `POST` | `/auth/logout` | Terminate session & clear cookies |
| `POST` | `/resumes/upload` | Upload & extract resume text (PDF/TXT) |
| `POST` | `/interviews` | Create a new interview session (Technical, Behavioral, or Mixed) |
| `POST` | `/interviews/{id}/next-question` | Fetch next adaptive interview question with RAG/STAR context |
| `POST` | `/interviews/{id}/submit-answer` | Submit answer for evaluation & receive dimensional feedback |
| `GET` | `/interviews/{id}/question-audio` | Stream ElevenLabs audio TTS for the active question |
| `GET` | `/interviews/{id}/results` | Retrieve final performance report & score breakdown |
| `GET` | `/health` | Service health status |

---

## Deployment Readiness Notes

- **Docker Containerization**: The PostgreSQL service with `pgvector` is defined in `docker-compose.yml`. For full-stack deployment, backend and frontend containers can be coordinated via multi-stage Dockerfiles.
- **CORS & Environment Separation**: Set `ENVIRONMENT=production`, adjust `FRONTEND_URL` and `BACKEND_URL` in `.env`, and generate a 64-character random string for `JWT_SECRET`.
- **Database Migrations**: In production pipelines, run `alembic upgrade head` as part of the deployment task before container startup.
- **Managed Vector Store**: When migrating to managed cloud PostgreSQL (AWS RDS, Supabase, Neon), ensure the `vector` extension is enabled.
