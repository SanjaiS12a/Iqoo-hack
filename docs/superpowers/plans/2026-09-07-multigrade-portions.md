# Multi-Grade Portions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Grade 1–12 physical database routing, multi-class teacher assignments, one-class student enrollment, portion upload/review/publish, and portion-scoped learning to ClassMind.

**Architecture:** Keep identities and assignments in a control database. Route all academic operations through `GradeDatabaseRegistry`, which owns twelve separate SQLite/PostgreSQL database connections. A provider-neutral content service turns PDF/image uploads into editable draft portions before teacher publication.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite/PostgreSQL, pypdf, OpenAI-compatible and Gemini provider adapters, React, TypeScript, TanStack Query, Vitest, Pytest.

**Spec:** `docs/superpowers/specs/2026-09-07-multigrade-portions-design.md`

## Global Constraints

- Support Grades 1–12 with physically separate academic databases.
- A student has exactly one active classroom assignment; a teacher may have many.
- Grade routing is derived from an authorized control-database assignment.
- Portion extraction always creates an editable draft and never auto-publishes.
- Published section portions exclusively scope student questions and plans.
- Demo mode remains usable without an API key or local model.

---

### Task 1: Control and grade database split

**Files:**
- Create: `backend/app/academic_models.py`
- Create: `backend/app/grade_database.py`
- Modify: `backend/app/models.py`
- Modify: `backend/app/services.py`
- Test: `backend/tests/test_multigrade.py`

**Interfaces:**
- Produces: `GradeDatabaseRegistry.session(grade: int) -> ContextManager[Session]` and `initialize(grade: int) -> None`.
- Produces: control entities `Classroom`, `TeacherAssignment`, and single `User.class_id` student assignment.

- [x] Write a failing test creating Grade 2 and Grade 9 classes and asserting `grade_02.db` and `grade_09.db` contain independent academic tables and records.
- [x] Implement separate declarative bases, grade URL validation, engine caching, and seeded Grade 9 migration data.
- [x] Run the multigrade routing test and the existing API suite.

### Task 2: Role assignments and classroom authorization

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/schemas.py`
- Test: `backend/tests/test_multigrade.py`

**Interfaces:**
- Produces: `GET /api/teacher/classes`, `GET /api/admin/grades`, `POST /api/admin/classes`, `POST /api/admin/classes/{id}/teachers`, and `POST /api/admin/classes/{id}/students/{student_id}`.
- Academic teacher routes use `/api/teacher/classes/{class_id}/...` and reject unassigned classrooms.

- [x] Add failing tests proving a teacher may access two assigned classes, cannot access another teacher's class, and a student move replaces the prior assignment.
- [x] Add administrator authorization, assignment services, and class-aware teacher routes.
- [x] Run authorization and legacy compatibility tests.

### Task 3: Portion upload, extraction, review, and publish

**Files:**
- Create: `backend/app/content_ai.py`
- Create: `backend/app/storage.py`
- Modify: `backend/app/academic_models.py`
- Modify: `backend/app/main.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_portions.py`

**Interfaces:**
- Produces: multipart `POST /api/teacher/classes/{class_id}/portions`, draft read/update routes, and idempotent publish route.
- Produces: `ContentIntelligenceProvider.extract(filename, media_type, bytes) -> ExtractedPortion`.

- [x] Add failing tests for valid PDF/image uploads, invalid signatures, draft extraction, editable topics/questions, publish validation, and unassigned-class denial.
- [x] Implement local storage, deterministic extraction, OpenAI-compatible provider wiring, Gemini configuration boundary, draft persistence, and publication.
- [x] Run portion tests and the full backend suite.

### Task 4: Portion-scoped student learning

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/services.py`
- Test: `backend/tests/test_portions.py`

**Interfaces:**
- Existing student overview, questions, submission, doubts, and study-plan endpoints resolve the student's control-plane class and matching grade database.

- [x] Add a failing test showing a Grade 2 student sees only their published section portion and receives a plan containing only that portion's topics.
- [x] Route student operations through the grade registry and filter by section plus published portion.
- [x] Run all backend tests.

### Task 5: Administrator and multi-class teacher interface

**Files:**
- Create: `frontend/src/pages/AdminApp.tsx`
- Create: `frontend/src/pages/PortionsPage.tsx`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Layout.tsx`
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/pages/TeacherApp.tsx`
- Modify: `frontend/src/pages/StudentApp.tsx`
- Modify: `frontend/src/index.css`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes control and portion APIs; produces administrator Grade 1–12 management, teacher class switcher, upload/review/publish UI, and student active-portion context.

- [x] Add failing UI tests for administrator entry and teacher class switching.
- [x] Implement role shells, class selector, grade overview, portion workflow, and class-scoped screens.
- [x] Run frontend tests and production build.

### Task 6: Delivery migration and verification

**Files:**
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docker-compose.yml`
- Modify: `backend/Dockerfile`

**Interfaces:**
- Produces a one-command demo with control plus Grade 1–12 databases and documented OpenAI, Gemini, local, and demo modes.

- [x] Document demo accounts, database files, provider configuration, portion workflow, and production database template.
- [x] Start the upgraded services and exercise administrator, teacher upload/publish, and student consumption in the browser.
- [x] Run fresh backend tests, frontend tests/build, inspect database files and git diff, then commit the finished migration.
