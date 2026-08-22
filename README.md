# Large Language Models for Technical Interview Preparation

## Project Overview

An LLM-powered technical interview preparation platform developed as a Software Engineering project.

The system is designed to help users prepare for technical interviews through personalized interview questions, adaptive AI-driven interviews, answer evaluation, performance feedback, and progress tracking.

The project uses Large Language Models as an intelligent component within a structured software engineering architecture.

## Technology Stack

### Frontend

- React
- Vite
- React Router
- Tailwind CSS
- Axios
- ESLint
- Prettier

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic Settings
- SQLAlchemy
- Psycopg
- Alembic
- Ruff
- Black

### Database

- PostgreSQL

### Development and DevOps

- Docker
- Docker Compose
- Git
- Pre-commit
- VS Code

## System Architecture

The current system follows a layered architecture in which the React frontend communicates with the FastAPI backend, and the backend manages communication with PostgreSQL.

                 User
                   │
                   ▼
           React Frontend
          localhost:5173
                   │
                Axios
                   │
                   ▼
           FastAPI Backend
          localhost:8000
                   │
               SQLAlchemy
                   │
                   ▼
        PostgreSQL Database
          Docker / localhost:5433

## Component Responsibilities

### Frontend

Responsible for:

1. User interface
2. Client-side routing
3. User interaction
4. API communication
5. Displaying results and feedback

### Backend

Responsible for:

1. API endpoints
2. Business logic
3. Configuration
4. Authentication and authorization in future phases
5. AI/LLM integration in future phases
6. Database operations

### Database

Responsible for:

1. Persistent application data
2. User information
3. Resume data
4. Interview sessions
5. Interview messages
6. Performance reports

## Project Structure

LLM-Interview-Preparation/
│
├── frontend/
│ └── src/
│ ├── components/
│ ├── context/
│ ├── hooks/
│ ├── layouts/
│ ├── pages/
│ ├── services/
│ └── utils/
│
├── backend/
│ ├── app/
│ │ ├── ai/
│ │ ├── api/
│ │ ├── core/
│ │ ├── models/
│ │ ├── repositories/
│ │ ├── schemas/
│ │ ├── services/
│ │ └── utils/
│ │
│ ├── alembic/
│ ├── tests/
│ ├── requirements.txt
│ └── alembic.ini
│
├── docs/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

## Backend Layer Responsibilities

1. api/ — API routes and endpoints
2. core/ — Configuration and database setup
3. models/ — SQLAlchemy database models
4. schemas/ — Pydantic request/response schemas
5. services/ — Application and business logic
6. repositories/ — Database access logic
7. ai/ — LLM-related functionality
8. utils/ — Shared utility functions

## Running the Project

### Prerequisites

Make sure the following are installed:

- Node.js and npm
- Python
- Docker Desktop
- Git

### 1. Start PostgreSQL

From the project root:
powershell
docker compose up -d

The PostgreSQL container runs on:
localhost:5433

To verify the container:
docker ps

### 2. Start the Backend

Open a terminal in the backend directory:
cd backend

Activate the Python virtual environment:
.\.venv\Scripts\Activate.ps1

Start the FastAPI server:
uvicorn app.main:app --reload

The backend will be available at:
http://127.0.0.1:8000

FastAPI Swagger documentation:
http://127.0.0.1:8000/docs

Health check:
http://127.0.0.1:8000/health

### 3. Start the Frontend

Open another terminal in the frontend directory:
cd frontend

Install dependencies if required:
npm install

Start the development server:
npm run dev

The frontend will be available at:
http://localhost:5173

### 4. Database Migrations

Alembic is used to manage database schema changes.

Check the current migration:
alembic current

Create a new migration after modifying database models:
alembic revision --autogenerate -m "describe change"

Apply migrations:
alembic upgrade head

### 5. Stop PostgreSQL

When finished working:
docker compose down

This stops the PostgreSQL container while preserving the database volume.
