# ClassMind — AI Teaching Co-Pilot

ClassMind is a complete school demo covering Grade 1 through Grade 12. A control database manages identities and assignments, twelve physically separate grade databases store academic work, and uploaded class portions drive questions, tutoring, analytics, and study plans.

## Working demo

Requirements: Python 3.12+ and Node.js 22+.

From PowerShell in the project directory:

```powershell
.\start-demo.ps1
```

Open [http://localhost:5173](http://localhost:5173). The first run installs dependencies. The API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

Demo accounts use password `demo1234`:

- Student: `aarav@classmind.demo`
- Teacher: `meera@classmind.demo`
- Administrator: `admin@classmind.demo`

The login screen provides one-click access to all three roles. Teachers have multiple assigned classes; sections contain 20–30 synthetic learners. Exam-frequency values are illustrative demo weights.

## Run services separately

Backend:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

The demo creates `backend/classmind_control.db` plus `backend/grade_databases/classmind_grade_01.db` through `classmind_grade_12.db`. Uploaded portion files are kept under `backend/uploads/` and are excluded from Git.

## Enable automatic AI fallback

Copy `.env.example` to `backend/.env`, then set:

```env
AI_PROVIDER=auto
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.4-mini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash
```

The keys are read only by FastAPI. The browser never receives them. Each AI operation tries OpenAI first, then Gemini, then the built-in deterministic demo provider so the classroom workflow remains available during remote API failures. The OpenAI provider uses the Responses API and Pydantic Structured Outputs for answer diagnosis and tutoring.

To force only OpenAI, use `AI_PROVIDER=openai`.

To force only Gemini through its OpenAI-compatible endpoint:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-3.6-flash
```

Local OpenAI-compatible model server:

```env
AI_PROVIDER=local
LOCAL_AI_BASE_URL=http://localhost:11434/v1
LOCAL_AI_MODEL=your_vision_capable_model
```

The selected provider powers portion extraction, answer diagnosis, tutoring, and re-teach generation. A local model must accept image input to extract photographed pages.

## Demo walkthrough

1. Enter as **Administrator** and inspect the twelve physically separated grade databases and their classroom sections.
2. Open **Assignments** to assign a teacher to several classes or move a student into exactly one class.
3. Enter as **Teacher**, switch between Grade 9A and Grade 6B, and confirm every dashboard changes with the selected class.
4. Open **Portions**, upload `demo-assets/grade-9-fractions-portion.pdf` (or your own PDF/PNG/JPEG), review the extracted draft, edit its topics, and publish it.
5. Enter as **Student** to see only Grade 9A's published portion, generated practice, and portion-scoped study plan.
6. Submit `2x = 10 - 4, so x = 7`, return as the teacher, and generate a focused re-teach from the class signal.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
npm test
npm run build
```

## Docker

```powershell
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). Docker initializes one PostgreSQL control database plus twelve distinct grade databases; local development uses thirteen SQLite files.

## Project structure

```text
backend/app/       FastAPI routes, control/grade routing, AI providers, uploads
backend/tests/     API and authorization integration tests
frontend/src/      React pages, shared components, API client, design system
docs/              Architecture and implementation plan
docker-compose.yml Full PostgreSQL-backed deployment stack
```

## Production notes

Set a strong `JWT_SECRET`, a managed PostgreSQL `DATABASE_URL`, exact `CORS_ORIGINS`, and the OpenAI settings. The demo uses bearer tokens in browser storage for simple judging; a public production deployment should move sessions to secure HTTP-only cookies and add rate limiting, password reset, audit logging, and real exam-question provenance.
