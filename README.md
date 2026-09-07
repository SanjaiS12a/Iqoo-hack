# ClassMind — AI Teaching Co-Pilot

ClassMind is a complete hackathon demo of a closed classroom learning loop: a learner shows their working, the system identifies a specific misconception, the teacher sees class-level patterns, and the learner receives a prioritized revision plan.

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

The login screen provides one-click access to both accounts. Seed activity represents a synthetic 40-learner classroom. Exam-frequency values are illustrative demo weights.

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

SQLite is created and seeded automatically at `backend/classmind.db`.

## Enable OpenAI

Copy `.env.example` to `backend/.env`, then set:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.4-mini
```

The API key is read only by FastAPI. The browser never receives it. The OpenAI provider uses the Responses API and Pydantic Structured Outputs for answer diagnosis and tutoring. Demo mode remains the default until a key is configured.

## Demo walkthrough

1. Enter as **Student**, open **Practice**, choose “Solving linear equations,” and submit `2x = 10 - 4, so x = 7`.
2. Review the precise transposition misconception and micro-explanation.
3. Sign out, enter as **Teacher**, and see the updated misconception count in **Class pulse**.
4. Click the wand beside the top misconception to generate a two-minute re-teach script.
5. Return as the student, open **Ask ClassMind**, and ask “Why does a minus sign change when I move a term?”
6. Open **My study plan**, generate priorities, and complete an item.

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

Open [http://localhost:3000](http://localhost:3000). Docker uses PostgreSQL; local development uses SQLite.

## Project structure

```text
backend/app/       FastAPI routes, AI providers, models, auth, seed data
backend/tests/     API and authorization integration tests
frontend/src/      React pages, shared components, API client, design system
docs/              Architecture and implementation plan
docker-compose.yml Full PostgreSQL-backed deployment stack
```

## Production notes

Set a strong `JWT_SECRET`, a managed PostgreSQL `DATABASE_URL`, exact `CORS_ORIGINS`, and the OpenAI settings. The demo uses bearer tokens in browser storage for simple judging; a public production deployment should move sessions to secure HTTP-only cookies and add rate limiting, password reset, audit logging, and real exam-question provenance.
