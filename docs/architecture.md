# System Architecture

## 1. Overview

The system follows a layered architecture consisting of a React frontend, FastAPI backend, and PostgreSQL database.

The architecture is designed to maintain separation of concerns and allow future modules such as authentication, resume analysis, LLM integration, interview evaluation, RAG, and analytics to be added without restructuring the entire application.

## 2. High-Level Architecture

                         User
                           │
                           ▼
                  ┌─────────────────┐
                  │ React Frontend  │
                  │   Vite + React  │
                  └────────┬────────┘
                           │
                         Axios
                           │
                           ▼
                  ┌─────────────────┐
                  │ FastAPI Backend │
                  │ Python + Uvicorn│
                  └────────┬────────┘
                           │
                       SQLAlchemy
                           │
                           ▼
                  ┌─────────────────┐
                  │   PostgreSQL    │
                  │ Docker Container│
                  └─────────────────┘

## 3. Frontend Layer

The frontend is responsible for user interaction and presentation.

Technologies:

1. React
2. Vite
3. React Router
4. Tailwind CSS
5. Axios

Responsibilities:

1. User interface
2. Client-side routing
3. Form handling
4. API communication
5. Displaying system responses
6. Future interview interface
7. Future dashboard and reports

## 4. Backend Layer

The backend provides the API and application logic.

Technologies:

1. Python
2. FastAPI
3. Uvicorn
4. SQLAlchemy
5. Pydantic
6. Psycopg

Responsibilities:

1. API endpoints
2. Business logic
3. Request validation
4. Authentication in future phases
5. Resume processing in future phases
6. LLM integration in future phases
7. Interview management
8. Database communication

## 5. Database Layer

PostgreSQL is used as the persistent data store.

- Current Configuration:
- Database: interview_db
- User: interview_user
- Host: localhost
- Port: 5433

PostgreSQL is executed inside a Docker container.

Planned Entities:
The final application is expected to contain -

1. Users
2. Resumes
3. Interview Sessions
4. Interview Messages
5. Reports

## 6. Backend Package Structure

backend/
└── app/
├── ai/
├── api/
├── core/
├── models/
├── repositories/
├── schemas/
├── services/
└── utils/

Responsibilities:

1. ai/ - LLM and AI-related functionality
2. api/ - API routes and endpoints
3. core/ - Configuration and database setup
4. models/ - SQLAlchemy database models
5. repositories/ - Database access operations
6. schemas/ - Pydantic request/response models
7. services/ - Application and business logic
8. utils/ - Shared utility functions

## 7. Data Flow

User
↓
React Frontend
↓
FastAPI Backend
↓
Interview / Resume Service
↓
Prompt Builder
↓
LLM Service
↓
Optional RAG Service
↓
LLM Response
↓
Evaluation Service
↓
PostgreSQL
↓
Frontend

## 8. Development and Database Management

The project uses:

1. Git for version control
2. Pre-commit for automated checks
3. Ruff for Python linting
4. Black for Python formatting
5. ESLint for frontend linting
6. Prettier for frontend formatting
7. Alembic for database migrations
8. Docker Compose for local PostgreSQL

## 9. Future Architecture Extensions

Future phases will add:

Authentication and authorization
Resume analysis
LLM-powered interview generation
Adaptive interview logic
Answer evaluation
Performance reports
Dashboard analytics
Voice and speech processing
Retrieval-Augmented Generation
Research evaluation modules
Production deployment
