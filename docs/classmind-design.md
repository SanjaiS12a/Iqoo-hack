# ClassMind implementation design

## Scope
Build a runnable full-stack teaching co-pilot for Class 9 mathematics, focused on linear equations, with teacher and student accounts. Implement all four core flows and the optional text/code skilling flow. Include responsive UI, persistent storage, seed data, tests, deployment configuration, and setup documentation.

## Architecture and alternatives
Recommended: React + TypeScript frontend, FastAPI backend, SQLAlchemy persistence with PostgreSQL for deployment and SQLite for immediate local use. Five-second dashboard polling follows the brief and avoids extra realtime infrastructure. Backend-only OpenAI Responses API integration keeps credentials private.

Alternative: Supabase authentication, PostgreSQL, and realtime reduce hosted infrastructure work but require an external project before full local testing. Alternative: Express uses one language throughout but offers less direct Python model validation. Choose FastAPI with portable database support for a self-contained handoff.

## Authentication and data boundaries
Provide registration, login, logout, password hashing, expiring server-validated sessions, teacher/student roles, and class membership. Students access their own answers, doubts, and plans; teachers access their own classes. Class creation and join codes support onboarding without allowing users to grant themselves access to arbitrary classes. Secrets live only in environment variables.

## Student experience
A student home shows progress, current weak concepts, and next practice steps. Practice presents a seeded question bank and accepts typed working. Submission results show correctness, a canonical misconception tag, and a short explanation. Doubt tutoring stores conversation entries and associated concepts; browser speech input is progressive enhancement with typed input always available. Revision plans rank weak topics against illustrative exam-frequency weights, explain each priority, link practice questions, and persist checklist completion. A skilling page supports text/code evidence against seeded rubrics.

## Teacher experience
A dashboard shows participation, accuracy, recent submissions, topic trends, and misconceptions ranked by distinct affected students. Include class selection, loading/empty/error states, refresh status, and student detail views. Generate and save targeted two-minute re-teach scripts. Subsequent correct answers update current weakness without deleting historical evidence. Doubt-derived needs are identifiable separately from confirmed incorrect answers.

## AI and ranking
Define validated structured schemas and a canonical concept/misconception taxonomy. OpenAI receives question context and untrusted student text with strict response validation, bounded requests, and timeouts. Provider failure returns an actionable error and does not fabricate successful diagnosis. An explicit demo provider offers curated deterministic examples and labels its limitations; uncertain freeform work is marked as needing review. API-backed tutoring and assessment require the user's OpenAI API key. Revision ranking is deterministic and explainable using active weakness, recency, and exam weight; optional AI text enriches explanations without changing recorded scores.

## Data
Tables cover users, classes, memberships, questions, submissions, doubts, misconception events, study plans/items, re-teach scripts, skill checkpoints/evidence, and sessions. Aggregations distinguish event counts from distinct students. Seed one teacher, a sample class, student accounts, questions, and clearly identified synthetic classroom activity. Exam weights are illustrative, not claimed to come from verified past papers.

## UI direction
Use a polished academic workspace: warm neutral background, dark navy text, teal accents, readable cards, a persistent desktop sidebar, and compact mobile navigation. Separate student and teacher navigation with clear role identity. Use accessible labels, keyboard controls, visible validation, and responsive charts.

## Delivery and verification
Deliver frontend/backend source, dependency lockfiles, environment examples, database initialization and seed commands, local launch scripts, Docker configuration, deployment instructions, and a three-minute demo walkthrough. Test authentication and class isolation, diagnosis validation, persistence, distinct-student aggregation, revision ordering/completion, and provider failures. Run frontend type checking/build and backend integration tests, then inspect critical browser flows. External hosting and live OpenAI verification depend on credentials and a deployment destination; document these honestly.
