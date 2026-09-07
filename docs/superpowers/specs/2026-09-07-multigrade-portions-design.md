# ClassMind Multi-Grade Classroom and Portion Design

## Objective

Extend the working ClassMind demo into a school structure covering Grade 1 through Grade 12. Authentication and assignments live in one central database. Each grade has a physically separate academic database. Teachers manage one or more assigned classroom sections, each student belongs to exactly one section, and every section has independent uploaded portions, generated learning content, assessments, analytics, and study plans.

## Roles and ownership

The system has three roles:

- Administrators create sections for Grades 1–12, assign one or more teachers, and assign each student to exactly one active section.
- Teachers can access only assigned sections. A teacher may teach sections in multiple grades and switches the active classroom before accessing portions or analytics.
- Students access only their assigned section and its published portions.

Removing or changing an assignment changes future access without deleting historical academic records. The administrator workflow is included in the demo with seeded accounts and sections.

## Database topology

The application uses thirteen databases:

- `classmind_control` stores users, credentials, roles, classroom definitions, teacher assignments, each student's single classroom assignment, grade database routing, and audit events.
- `classmind_grade_01` through `classmind_grade_12` store academic data for the corresponding grade.

The local demo uses thirteen separate SQLite files. PostgreSQL deployment creates thirteen distinct databases on the configured server. A grade connection registry lazily creates SQLAlchemy engines and sessions from validated grade numbers. Grade selection always comes from an authorized classroom assignment in the control database; clients cannot select a database by sending an arbitrary connection name.

Each grade database contains section-scoped portions, uploaded-file metadata, extracted topics, learning outcomes, questions, submissions, doubts, misconception events, study plans and items, and re-teach scripts. Every academic query also filters by section identifier, so sections such as 9A and 9B remain isolated inside the Grade 9 database.

## Portion ingestion

A teacher selects an assigned section and uploads a PDF, JPG, JPEG, or PNG up to 20 MB. The backend verifies file type and signature, stores the original under a grade- and section-specific directory in demo mode, and records a `processing` portion row. Production storage uses an S3-compatible object store through the same storage interface.

PDFs are inspected for embedded text. Pages without usable text are rendered as images. Image uploads and scanned pages go to a vision-capable provider. The provider returns validated structured data containing:

- subject and portion title;
- chapters, topics, subtopics, and their sequence;
- learning outcomes and estimated teaching time;
- suggested questions, expected answers, difficulty, and illustrative exam weight;
- canonical misconception tags and student-facing explanations;
- study-plan priority hints.

Extraction creates a draft only. The teacher can edit, add, remove, and reorder all generated topics and questions. Publishing snapshots the approved draft and makes it available to that section's students. Older published portions remain available in history and can be archived; only currently published portions feed new practice and study-plan generation.

## AI providers

The backend exposes one `ContentIntelligenceProvider` interface with OpenAI, Gemini, local, and deterministic demo implementations. Configuration selects one provider:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.4-mini
```

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=configured-model-name
```

```env
AI_PROVIDER=local
LOCAL_AI_BASE_URL=http://localhost:11434/v1
LOCAL_AI_MODEL=configured-vision-model
```

The local adapter uses an OpenAI-compatible endpoint and requires the configured model to support image input for scanned content. The deterministic provider supplies a complete seeded extraction for demonstrations without any model or key. A failed, timed-out, or schema-invalid extraction marks the portion `failed`, preserves the upload, and offers retry; it never publishes partial content.

## Student behavior

The student shell displays grade, section, and active portion. Practice questions come only from published portions in the student's section. Doubt tutoring receives the active portion context. Study plans rank misconceptions only against topics contained in that section's published portions. When no portion is published, the student sees a clear waiting state rather than global sample questions.

## Teacher behavior

The teacher shell adds a persistent class selector and class-management overview. Changing the active class reloads portions, students, dashboard metrics, recent activity, and re-teach history from that class's grade database. The Portions page provides upload, processing state, draft review, publishing, and archive actions. Dashboard aggregates never combine classes unless an explicit teacher overview card reports high-level counts without exposing student-level records.

## Administrator behavior

The administrator shell lists Grades 1–12, sections, teachers, and enrollment counts. Administrators can create a section, assign or unassign teachers, and move a student to one section. Creating the first section for a grade initializes that grade database automatically. Assignment validation prevents duplicate section codes within a grade and prevents a student from holding two active classroom assignments.

## API boundaries

Control-plane endpoints cover login, role-aware session details, grade/section management, teacher assignments, student placement, and each user's allowed classrooms. Academic endpoints include a classroom ID in the route. A dependency resolves the classroom in the control database, verifies the current user's assignment, chooses the matching grade database, and injects a section-scoped academic session.

File upload uses multipart form data. Draft edits use validated JSON. Publishing is idempotent and requires a draft with at least one topic and one question. Responses never expose filesystem paths, database URLs, provider keys, or content belonging to another section.

## UI design

The existing visual language remains. Teachers receive a class switcher in the sidebar, a class overview, and a Portions workspace with upload progress and an editable review screen. Administrators receive a school overview with a Grade 1–12 grid and section assignment panels. Students see their class and active portion in the top bar. Desktop and mobile navigation preserve the active classroom context.

## Verification

Backend integration tests will verify grade routing, physical database creation, teacher multi-class access, denial of unassigned classes, single-class student enforcement, section isolation within a grade, upload validation, deterministic extraction, draft editing, publishing, and portion-scoped study plans. Provider adapters will validate structured responses and error paths without calling paid APIs in tests.

Frontend tests will cover role entry, teacher class switching, portion upload/review/publish states, administrator assignments, and a student's published-portion view. Final verification will run backend tests, frontend tests and build, then exercise administrator setup, teacher upload/publish, and student consumption in the browser.

## Demo data and operational limits

The demo includes an administrator, teachers assigned across several grades, sections with 20–30 synthetic students, and sample portions. Existing Grade 9A activity is migrated into the Grade 9 database. Live OpenAI, Gemini, and local-model quality depends on credentials or the user's local endpoint; deterministic mode remains fully runnable. Production deployment must supply managed database URLs, object storage, a strong session secret, rate limiting, and secure HTTP-only sessions.
