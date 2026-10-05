# InsightPrep Project Context

**Status:** architecture reference, updated 2026-10-03. This document distinguishes verified repository facts from proposed RAG work. RAG is **not implemented**.

## 1. Project overview

InsightPrep is an AI-powered interview-preparation platform. Authenticated users upload a PDF or DOCX resume, receive structured resume analysis, complete fixed or adaptive mock interviews, submit written or browser-transcribed answers, and receive scored feedback, history, and performance analytics. The system also provides ElevenLabs question text-to-speech.

The next planned feature is meaningful retrieval-augmented generation (RAG): curated technical-interview knowledge should ground relevant technical questions and technical answer feedback without replacing the current LLM providers or disrupting the existing interview engine.

Repository: `C:\Users\hp\Documents\LLM-Interview-Preparation`  
GitHub: `https://github.com/PJscripts/InsightPrep`

## 2. Verified current architecture

### Application stack

| Layer | Verified implementation |
| --- | --- |
| Frontend | React 19, Vite, React Router, Axios, Tailwind; frontend development server defaults to port 5173. |
| Backend | FastAPI application in `backend/app/main.py`; Uvicorn development server defaults to port 8000. |
| Persistence | PostgreSQL accessed through SQLAlchemy 2 and Psycopg. `docker-compose.yml` exposes PostgreSQL 17 on host port 5433. |
| Schema changes | Alembic, configured in `backend/alembic/env.py` with `Base.metadata` and `DATABASE_URL`. |
| Quality tools | Ruff and Black for backend; ESLint and Prettier dependencies for frontend; pre-commit runs Ruff (with `--fix`) and Black. |

The existing `README.md` and `docs/architecture.md` still describe several formerly future components. This file records the implementation as currently verified in source rather than relying on those older descriptions.

### Backend packages and API routes

`backend/app/main.py` registers these routers:

| Route group | Verified routes / responsibility |
| --- | --- |
| `/auth` | `POST /register`, `POST /login`, `GET /me`, `POST /logout`; login writes an HTTP-only access-token cookie. |
| `/resumes` | `POST /upload` accepts PDF/DOCX up to 5 MB, extracts text, analyzes it, persists the result; `GET /profile` returns the latest analyzed resume profile. |
| `/interviews` | `POST /sessions`, current-question retrieval, question audio, answer submission, history, progress, session results, and abandonment. |
| `/health` | Simple unauthenticated health response. |

The application uses dependency-based authentication (`app.core.dependencies`) and SQLAlchemy sessions from `app.core.database.get_db`.

### Database models and migrations

Current SQLAlchemy models are `User`, `Resume`, `InterviewSession`, `InterviewQuestion`, and `InterviewAnswer`.

* `resumes` stores metadata, extracted plain text (`extracted_text`), analysis status, structured JSONB analysis (`analysis`), and an optional score. A resume belongs to a user.
* `interview_sessions` references a user and optional resume. It records fixed/adaptive mode, type, difficulty, question count and progress, adaptive topic state, and the current question/evaluation provider names.
* `interview_questions` stores ordered question text and type, with a unique `(session_id, question_number)` constraint.
* `interview_answers` stores one answer per question with score, feedback, and JSON skill dimensions.

Alembic migration history creates users, resumes, and interview tables; adds per-session provider tracking; adds question uniqueness; adds adaptive state; and adds answer skill dimensions. No vector tables, vector extension, RAG models, or RAG migrations exist.

## 3. Frontend structure

Verified routes in `frontend/src/App.jsx` are:

* Public: `/`, `/login`, `/register`.
* Authenticated: `/dashboard`, `/resume`, `/interview`, `/history`, `/performance`, `/interview/:sessionId`, and `/interview/:sessionId/result`.

Important pages are `Home`, `Login`, `Register`, `Dashboard`, `Resume`, `InterviewSetup`, `Interview`, `InterviewResult`, `History`, and `Performance`. `Interview.jsx` requests current questions, submits answers, fetches ElevenLabs audio, and uses browser `SpeechRecognition`/`webkitSpeechRecognition`. The RAG phase must not redesign or change these components.

## 4. Authentication and resume flow

1. A user registers or logs in through `/auth`; login creates an HTTP-only JWT cookie.
2. Resume upload validates extension and size, saves the file under `uploads/resumes`, then extracts text with `pypdf` (PDF) or `python-docx` (DOCX).
3. The resume analyzer receives up to 20,000 characters and returns structured fields: `skills`, `experience`, `education`, `projects`, `strengths`, `skill_gaps`, and `recommended_topics`.
4. The raw extracted text and structured result are stored in `resumes`; `analysis_status` becomes `analyzed`.
5. New interviews use the latest analyzed resume. Question generation receives the stored structured analysis directly.

### Resume/RAG decision (verified and proposed)

**Verified:** the current design already preserves raw resume text and passes structured analysis into prompts. `get_candidate_topics` derives topics from recommended topics, skills, projects, and experience.

**Decision for proposed RAG:** do not initially vectorize resumes. The structured analysis is the correct default personalization signal and avoids an unnecessary per-user vector corpus. Reconsider resume retrieval only if future resumes exceed prompt limits or questions need exact, granular evidence not represented by the structured fields.

## 5. Interview, generation, and evaluation flows

### Session and adaptive behavior

`POST /interviews/sessions` requires the latest analyzed resume, creates a session with configured mode/type/difficulty, and generates its first question. Fixed sessions support 3, 5, or 10 questions. Adaptive sessions begin with an introduction and run from 8 to 15 questions according to score, answer length, topic coverage, and per-topic follow-up state. The frontend currently exposes technical, HR, and mixed type options; HR/behavioural support remains a roadmap item because the requested next phase is RAG first.

Question history (previous questions, answers, and evaluations) is read from the database and passed to subsequent generations. The engine avoids repeated questions and chooses a follow-up or topic shift based on the session state.

### LLM provider routing and safeguards

| Workload | Primary → fallback → final fallback |
| --- | --- |
| Resume analysis | Gemini → Groq → Mock |
| Question generation | Groq → Gemini → Mock |
| Answer evaluation | Groq → Gemini → Mock |

Provider selection is settings-driven. `InterviewSession` persists whichever question or evaluation provider ultimately succeeded, and the API route logs each primary/fallback transition. The mock provider is deterministic and must remain available.

Gemini and Groq generator prompts contain structured resume context, interview configuration, current topic, history, and strategy. Both require exactly one concise question. Evaluator prompts contain the question, answer, resume context, a 0--10 rubric, and four dimensions: technical knowledge, problem solving, communication, and clarity. Evaluations are validated as JSON before persistence.

The provided configuration template sets `GEMINI_MODEL=gemini-3.6-flash` and `GROQ_MODEL=openai/gpt-oss-120b`; the Python settings default currently says `gemini-3.7-flash`. The effective deployed model is determined by the uncommitted local `.env`, which was intentionally not inspected. Resolve this documentation/default mismatch before deployment, but do not alter provider routing or models as part of the RAG implementation without approval.

## 6. Voice functionality and known limitation

Question audio is produced by `app.services.elevenlabs_tts` and requested at `/interviews/sessions/{id}/question/audio`. Browser speech recognition is implemented in the live interview page. ElevenLabs TTS is considered working. Browser STT transcription quality is a known limitation, deliberately deferred until after RAG and HR/behavioural interviewing. Neither system is in scope for RAG.

## 7. Product roadmap

### Completed

* Project foundation, authentication, resume upload/analysis, fixed and adaptive interview engines.
* Gemini/Groq/Mock integration, answer evaluation, feedback, dashboard/product UI.
* History and performance analytics, ElevenLabs TTS, browser STT integration.
* Reliability/security work, logging/regression testing as stated by the project roadmap, and initial GitHub commit/push.

### Partially completed / known limitations

* Adaptive intelligence, resume-aware interviewing, and analytics are present but remain subject to iterative quality work.
* Voice experience: TTS works; browser STT accuracy needs improvement.
* The repository contains `backend/tests/__init__.py` but no discovered substantive backend test modules. The claim of regression testing should therefore be treated as roadmap/history context, not current in-repository automated-test coverage.
* Runtime dependencies imported by resume/LLM services (including Google GenAI, Groq, `pypdf`, and `python-docx`) were not present in the inspected `backend/requirements.txt`; reconcile the manifest before relying on a clean environment.

### Remaining work (required order)

1. RAG integration
2. HR/behavioural interview support
3. Improve STT accuracy
4. Deployment

Forgot-password and email-verification work are intentionally excluded from this roadmap.

## 8. RAG implementation status and proposed architecture

### Status

Not implemented. There is no knowledge-document corpus, ingestion endpoint/command, chunker, embedding client, vector store, retrieval service, source metadata, or RAG test suite in the repository.

### Approved RAG decisions (2026-10-03)

* The initial corpus will contain a small set of clearly labelled, project-authored Markdown documents for DSA, DBMS, operating systems, computer networks, and OOP. It must not scrape websites or include copyrighted textbook material.
* Each source will have manifest metadata for title, topic, origin, and license/provenance. The corpus will be reviewed and expanded separately from implementation.
* Embeddings will use a local sentence-transformer behind an embedding-provider interface. Retrieval and embedding failures remain nonfatal and do not change Groq → Gemini → Mock routing.
* Retrieval traces will persist only source/chunk identifiers and similarity scores for relevant question/evaluation operations. They must not duplicate full passages or sensitive resume/answer text.
* The data model change will be additive.

The candidate exact runtime stack, migration shape, and first-milestone file plan are awaiting explicit approval before source, dependency, infrastructure, or migration changes begin.

### Milestone 1: embedding boundary (completed 2026-10-03)

The first implementation milestone adds only typed embedding results, a lazily loaded local sentence-transformer boundary, pytest setup, and tests. It does not connect RAG to routes, prompts, providers, the database, or Docker.

The boundary returns `disabled` only when RAG is intentionally configured off. Model-load, inference, malformed-vector, and empty-input conditions return a typed `unavailable` result and log unexpected failures at error level; no exception is allowed to reach an interview flow.

Dependency-resolution check: the manifest's prior `websockets==17.0.1` pin conflicts with `google-genai==2.19.0`, which requires `websockets>=13,<17`. The approved correction is `websockets==16.0`; a Python 3.14 dry run resolves with this value and the milestone packages.

Verification: the resolved manifest installed successfully and `pip check` reported no broken requirements. Five pytest cases passed for disabled operation, model-load failure, embedding-inference failure, invalid vectors, and valid lazy model caching. The tests use injected fakes and do not download or load the embedding model. Empty-corpus, retrieval-failure, and interview-flow regression tests remain for the retrieval and integration milestones because no retrieval path exists in milestone 1.

### Recommended minimal architecture

Use PostgreSQL with the `pgvector` extension for production and local development, retaining a lightweight deterministic in-memory fake only for unit tests. This fits the existing PostgreSQL/SQLAlchemy/Alembic stack, keeps metadata and vectors transactional, avoids operating a separate vector service, and is deployable at low cost for a student project. The Docker image will need to change from plain PostgreSQL to a pgvector-enabled PostgreSQL image when implementation begins.

Use a local sentence-transformer embedding model by default, e.g. a compact retrieval model run in the backend process or ingestion command. This avoids a new paid provider and keeps retrieval independent from Gemini and Groq. It requires model download/storage and CPU/RAM at ingestion/runtime. If future deployment limits make that impractical, introduce an optional embedding-provider interface with configuration, but never make question/evaluation availability depend on that provider.

Proposed data flow:

```text
Curated source files + manifest
  -> validated extraction -> normalized text -> semantic chunks
  -> local embeddings -> knowledge_documents / knowledge_chunks (PostgreSQL + pgvector)

Session topic + interview type + difficulty (+ question or answer when evaluating)
  -> RetrievalService (top-k, metadata filters, relevance threshold)
  -> optional bounded context with source IDs
  -> existing Groq/Gemini prompt -> existing fallback behavior
```

### Knowledge ingestion and metadata

Curated technical material is administrator-maintained, not user-uploaded. Store a stable `source_key`, human-readable title, domain/topic, source path or license reference, optional revision/hash, chunk index, normalized text, and embedding. Each retrieved passage should retain its document/chunk identity. Begin with plain UTF-8 Markdown/text; add PDF/DOCX knowledge-source extraction only after the base path is tested.

Chunk by headings first, then split oversized sections into roughly 350--500 token chunks with 50--75-token overlap. Keep metadata with every chunk. Reject empty chunks and deduplicate by content hash. Keep a bounded retrieval payload (for example, 3--5 passages and a character/token cap) to avoid swamping the current prompt.

### Retrieval behavior

* For technical question generation, search using interview type, current topic, difficulty, and candidate resume-derived topics. Filter out nontechnical materials and return only passages above a configurable relevance threshold.
* For technical answer evaluation, search primarily using the question; use the answer only as secondary query context. In the prompt, label passages as reference material, require the model to evaluate only the submitted answer, and prohibit treating passages as a complete grading rubric.
* For HR/mixed interviews, defer technical knowledge retrieval until the HR phase defines an appropriate corpus. Existing generators still work without retrieved context.
* No result, below-threshold result, empty corpus, embedding outage, or retrieval exception must yield an empty context and continue via the existing generator/evaluator and its Groq → Gemini → Mock path. Retrieval failure must never trigger a provider switch by itself.
* Initially log non-sensitive retrieval telemetry: query category, returned count, scores, source IDs, and fallback/empty-context reason. Do not log full resumes or answer text unnecessarily.

### Traceability

Initial source traceability belongs in backend persistence and logs. Store source/chunk IDs and retrieval scores associated with a question or answer only if the migration is approved. Do not display citations in the current UI and do not fabricate them. A later UI/API phase can expose verified source title and passage excerpt.

### Storage alternatives considered

| Option | Fit / trade-off | Decision |
| --- | --- | --- |
| PostgreSQL + pgvector | Matches existing DB, Alembic, Docker, ownership, backups, and eventual deployment; adds one extension/image and vector index migration. | Recommended. |
| Local file vector store | Very easy for a solo local demo, but adds a second persistence/backup/deployment concern and weakens multi-instance deployment. | Not recommended as the primary store. |
| Hosted vector database | Operationally convenient at scale but introduces cost, credentials, another vendor, and a network dependency. | Not justified for this project. |

## 9. Proposed implementation file-change plan (not executed)

Names below are proposed exact targets for approval; no source change has been made in this review phase.

### New files

| Proposed file | Purpose |
| --- | --- |
| `backend/app/models/knowledge_document.py` | SQLAlchemy model for curated source metadata. |
| `backend/app/models/knowledge_chunk.py` | Chunk text, vector embedding, content hash, metadata, and source relationship. |
| `backend/app/services/rag/types.py` | Typed retrieval result/context contracts, isolated from provider SDKs. |
| `backend/app/services/rag/embeddings.py` | Local embedding-provider interface and sentence-transformer implementation. |
| `backend/app/services/rag/chunking.py` | Deterministic normalization and heading-aware chunking. |
| `backend/app/services/rag/retrieval.py` | Optional, thresholded topic/question retrieval service. |
| `backend/app/services/rag/ingestion.py` | Idempotent knowledge-source ingestion orchestration. |
| `backend/scripts/ingest_knowledge_base.py` | Explicit operator command to ingest curated material; no public user-upload endpoint. |
| `backend/knowledge_base/README.md` | Curated corpus format, provenance, licensing, and ingestion instructions. |
| `backend/knowledge_base/manifest.example.yaml` | Safe example source manifest, with no copyrighted corpus included. |
| `backend/tests/services/test_rag_chunking.py` | Unit tests for deterministic chunking and metadata. |
| `backend/tests/services/test_rag_retrieval.py` | Retrieval thresholds, filters, empty corpus, and failure behavior. |
| `backend/tests/api/test_interview_rag_integration.py` | Regression tests proving empty/retrieval-failed paths preserve existing interview behavior. |
| `backend/alembic/versions/<revision>_add_rag_knowledge_tables.py` | Approved migration for pgvector extension, knowledge tables, indexes, and optional trace records. |

### Modified files

| Proposed file | Minimal change |
| --- | --- |
| `backend/app/models/__init__.py` | Import new RAG models so Alembic sees metadata. |
| `backend/app/core/settings.py` | Add new, optional RAG settings only; retain all current environment variable names. |
| `.env.example` | Document optional RAG defaults without secrets. |
| `backend/requirements.txt` | Add the selected local embedding/vector dependencies and reconcile already-imported runtime dependencies. |
| `docker-compose.yml` | Use a compatible pgvector PostgreSQL image; preserve the existing database service/volume/port behavior. |
| `backend/app/services/gemini_question_generator.py` | Accept optional retrieved context and include it in the existing prompt with grounding instructions. |
| `backend/app/services/groq_question_generator.py` | Same optional context contract and prompt insertion. |
| `backend/app/services/gemini_answer_evaluator.py` | Same optional context contract and bounded evaluation-reference prompt insertion. |
| `backend/app/services/groq_answer_evaluator.py` | Same optional context contract and bounded evaluation-reference prompt insertion. |
| `backend/app/api/interviews.py` | Retrieve before existing generation/evaluation calls; pass empty context on any retrieval failure; optionally persist trace metadata. |
| `backend/app/services/question_generator.py` and `backend/app/services/answer_evaluator.py` | Extend protocol signatures with an optional RAG context value so Mock remains callable without it. |
| Mock generator/evaluator files | Accept and ignore the optional context, preserving deterministic fallback output. |
| `PROJECT_CONTEXT.md` | Mark each approved RAG milestone complete only after implementation and verification. |

No frontend component, TTS/STT code, auth route, resume-analysis provider routing, or existing interview schema needs a change for the first RAG integration. Existing question/answer schemas can remain unchanged unless traceability is intentionally exposed later.

## 10. Risks and safeguards

| Risk | Safeguard |
| --- | --- |
| Retrieval degrades a working interview | Retrieval is optional, bounded, thresholded, and returns an empty context on any failure. |
| A new embedding dependency blocks providers | Embeddings are isolated behind a service; generation/evaluation proceed without them. |
| Incorrect retrieval becomes a grading oracle | Prompts define passages as supporting reference, preserve the existing rubric, and require evaluating only demonstrated answer content. |
| Prompt bloat/history regression | Apply strict top-k and text budget; retain current history and adaptive strategy unchanged. |
| Resume privacy or duplication | Keep structured resume analysis as personalization; do not ingest user resumes into the shared corpus. |
| Broken fallback routing | Keep current provider factories and route-level Groq → Gemini → Mock fallback; Mock accepts empty/ignored RAG context. |
| Existing database data disruption | Use additive Alembic migration only; do not rewrite existing tables or require backfill of resume/interview rows. |
| Untraceable corpus claims | Require source manifest/provenance and persist only real source/chunk IDs. |

## 11. RAG milestones and acceptance criteria

| Milestone | Expected result / files | Tests and acceptance criteria |
| --- | --- | --- |
| 1. Contracts and configuration | Add RAG types/settings and an empty-context implementation. | Unit tests prove absent configuration, empty corpus, and service errors return empty context without throwing. Existing interview tests/flows remain unchanged. |
| 2. Knowledge schema | Add models and additive Alembic migration; pgvector starts locally. | `alembic upgrade head` on a copy/local DB succeeds; prior tables/data remain readable; vector index and metadata constraints exist. |
| 3. Ingestion | Implement manifest validation, extraction, normalization, chunking, embeddings, and idempotent upsert. | Fixture documents produce stable chunks/metadata; rerun does not duplicate chunks; invalid source fails with actionable error. |
| 4. Retrieval quality | Implement filtered, thresholded top-k search and telemetry. | Known fixture queries retrieve expected source IDs; irrelevant queries return no context; retrieval service failure is nonfatal. |
| 5. Question grounding | Wire optional context into Gemini/Groq question prompts and Mock-compatible protocols. | Fixed 3/5/10 and adaptive paths work with empty context; seeded retrieval reaches the prompt; provider fallback remains intact. |
| 6. Evaluation grounding | Wire context into evaluator prompts and optional trace persistence. | JSON evaluation validation still works; retrieval-failed path returns normal evaluation; feedback is grounded but does not claim unsupported citation. |
| 7. Evaluation and release gate | Curate a small labelled query set and compare baseline vs RAG outputs. | Document precision@k/source relevance, duplicate-question rate, evaluator agreement/review, latency, and failure rate. Adopt RAG only if relevance improves without unacceptable latency or regressions. |

## 12. Development and verification commands

From the repository root:

```powershell
docker compose up -d
cd backend
.\.venv\Scripts\Activate.ps1
alembic current
alembic upgrade head
uvicorn app.main:app --reload
```

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev
npm run lint
npm run build
```

Backend lint/format commands, after dependencies are available:

```powershell
cd backend
ruff check .
black --check .
```

No substantive backend test command was discoverable from the inspected files. As part of RAG implementation, add and run `pytest` only after the project declares it as a test dependency; do not claim it currently runs from the checked-in manifest.

## 13. Environment configuration

Required existing configuration includes `DATABASE_URL`, `JWT_SECRET`, Gemini/Groq API keys and models, all resume/question/evaluation primary/fallback variables, `LLM_FINAL_FALLBACK`, timeout/retry variables, frontend/backend URLs, and ElevenLabs settings. `.env` files are ignored by Git; never commit secrets.

Proposed optional RAG settings should be new names, such as `RAG_ENABLED`, `RAG_EMBEDDING_PROVIDER`, `RAG_EMBEDDING_MODEL`, `RAG_TOP_K`, `RAG_MIN_SIMILARITY`, and `RAG_MAX_CONTEXT_CHARS`. Their defaults must leave RAG disabled or safely no-op when no corpus/embedding model is available. Exact names and defaults require approval with the selected embedding implementation.

## 14. Architecture decisions and constraints

* Preserve existing functionality; inspect before editing; prefer small, modular, testable changes.
* Do not replace Gemini or Groq, remove Mock, alter current provider routing, refactor unrelated services, or change existing environment-variable names without an approved technical reason.
* Do not modify frontend UI, TTS/STT, forgot-password, or email-verification work during RAG.
* Use curated technical knowledge, not unverified internet material or user resumes, for the shared RAG corpus.
* Do not install dependencies, create migrations, or implement RAG until the architecture and file plan are approved.
* Do not commit or push unless explicitly requested.

## 15. Decisions needed before implementation

1. **Corpus ownership and licensing:** approve the initial curated technical source set (recommended: project-authored Markdown notes or openly licensed material with a source manifest). This is required before ingestion can be implemented responsibly.
2. **Embedding runtime:** approve the recommended local sentence-transformer default, or specify a hosting/platform constraint that requires an optional external embedding provider instead.
3. **Trace persistence scope:** approve whether first release should store per-question/per-answer retrieved source IDs and scores for later auditability (recommended) or log them only initially. This determines whether an additional trace table/migration is included.

All other architecture choices above are recommendations designed to preserve the current app and can proceed after these decisions are made.
