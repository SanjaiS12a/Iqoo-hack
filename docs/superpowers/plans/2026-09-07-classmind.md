# ClassMind Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete local demo of the ClassMind student assessment, tutoring, revision, and teacher insight loops.

**Architecture:** A React TypeScript single-page application calls a FastAPI service. SQLAlchemy stores users, classes, questions, submissions, doubts, plans, and re-teach scripts in SQLite locally or PostgreSQL in production. An AI provider interface selects deterministic demo behavior or the OpenAI Responses API.

**Tech Stack:** React, TypeScript, Vite, Tailwind CSS, FastAPI, Pydantic, SQLAlchemy, SQLite/PostgreSQL, OpenAI Python SDK, Pytest, Vitest, Docker.

**Spec:** `docs/classmind-design.md`

## Global Constraints

- The backend owns AI credentials and data authorization.
- Demo mode must be useful without an API key and visibly identified.
- Teachers can read only their classes; students can read only their own personal records.
- Exam frequency values and seeded classroom activity must be labeled as illustrative demo data.
- Core layouts must work on desktop and mobile.

---

### Task 1: Backend domain and authentication

**Files:** `backend/app/config.py`, `backend/app/database.py`, `backend/app/models.py`, `backend/app/schemas.py`, `backend/app/auth.py`, `backend/tests/test_api.py`

**Interfaces:** Produces `create_app()`, bearer login tokens, role-aware current users, and SQLAlchemy entities used by later routes.

- [x] Write API tests for demo login, invalid credentials, and role isolation; run them and confirm they fail because the app is absent.
- [x] Implement configuration, models, password hashing, token authentication, and seed data.
- [x] Run the authentication tests and confirm they pass.

### Task 2: Assessment, tutoring, plans, and teacher APIs

**Files:** `backend/app/ai.py`, `backend/app/services.py`, `backend/app/main.py`, `backend/tests/test_api.py`

**Interfaces:** Produces `/api/student/*` and `/api/teacher/*` JSON endpoints; consumes authenticated user and database session.

- [x] Add failing tests for answer diagnosis persistence, distinct-student misconception aggregation, doubt logging, plan ordering/completion, and teacher authorization.
- [x] Implement the demo/OpenAI provider boundary, service logic, and routes with validated response schemas.
- [x] Run all backend tests and confirm they pass.

### Task 3: Student and teacher web application

**Files:** `frontend/src/api.ts`, `frontend/src/types.ts`, `frontend/src/App.tsx`, `frontend/src/components/*`, `frontend/src/pages/*`, `frontend/src/index.css`, `frontend/src/App.test.tsx`

**Interfaces:** Consumes the backend REST contract and produces role-specific responsive routes.

- [x] Add failing component tests for login and role navigation.
- [x] Implement the design system, authentication shell, student practice/doubts/plan pages, teacher dashboard, class insights, and re-teach generation.
- [x] Run frontend tests, type checking, and production build.

### Task 4: Runnable delivery and end-to-end verification

**Files:** `.env.example`, `README.md`, `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `.gitignore`

**Interfaces:** Produces documented local and container launch paths.

- [x] Add environment examples, startup/deployment documentation, Docker definitions, and demo credentials.
- [x] Start both services and exercise login, student submission, teacher aggregation, re-teach, doubt, and study-plan flows through the browser/API.
- [x] Run fresh backend tests and frontend test/build commands, inspect the final diff, and record any limitations.
