# RecoverAI — Architecture

## Current state (through Stage 2)

React / Vite frontend (src/)
│ HTTP (JSON), via src/services/api.ts
▼
FastAPI — backend/app/api/ (routes: request/response only)
│
▼
Repository layer — backend/app/repositories/ (typed, no route touches Mongo directly)
│
▼
DB layer — backend/app/db/ (Motor connection, indexes, collection names)
│ Motor (async MongoDB driver)
▼
MongoDB
├─ merchants
├─ customers
├─ payments
├─ payment_attempts
├─ recovery_cases
└─ audit_logs


Nothing skips a layer: routes never touch Motor directly, and the
frontend never talks to MongoDB or backend internals directly — only
`src/services/api.ts`.

**Layer boundaries, and why they exist:**

- **Frontend (`src/`)** never talks to MongoDB or the backend's internal
  modules directly. It only calls the functions in `src/services/api.ts`,
  which either return mock data or `fetch()` the FastAPI backend depending
  on `VITE_API_BASE_URL`. This stays true after Stage 2 — no frontend files
  were touched, and no real payments/customers/recovery endpoints exist yet
  for it to call (that's Stage 3).

- **API routes (`backend/app/api/`)** handle HTTP concerns only —
  request/response shapes, status codes. They do not run MongoDB queries
  themselves.

- **Repository layer (`backend/app/repositories/`)** is the only code
  permitted to run MongoDB queries. `BaseRepository` provides typed
  insert/find/count/delete operations against a single collection;
  `entities.py` wires each domain model to its collection. This means a
  future change to how data is stored (field renames, a different id
  scheme, a caching layer) touches one file per entity, not every route
  that happens to need that data.

- **Database layer (`backend/app/db/`)** owns the MongoDB connection
  lifecycle (`mongodb.py`), index definitions (`indexes.py`), and
  collection name constants (`collections.py`). Nothing outside this
  folder and `repositories/` imports Motor directly.

- **Models (`backend/app/models/domain.py`)** are Pydantic models shared
  by the repository layer and (in later stages) API request/response
  schemas. They currently cover: `Merchant`, `Customer`, `Payment`,
  `PaymentAttempt`, `RecoveryCase`, `AuditLog`.

## What's intentionally NOT here yet

- No ML model. `RecoveryCase.recovery_probability` is a plain stored
  float — nothing computes it yet. That's Stage 4.
- No AI agent. `RecoveryCase.recommended_action` and `AuditLog` are
  storage shapes only; no rules engine or LLM call produces them yet.
  That's Stage 5.
- No payment simulator. `PaymentAttempt` records the *result* of an
  attempt; nothing simulates one yet. That's Stage 6.
- No `/api/payments`, `/api/customers`, or `/api/recovery-cases`
  endpoints. Stage 2 only adds `GET /api/db/health`. The full read/write
  API surface is Stage 3.

## Target architecture (once all stages land)

Frontend → FastAPI API layer → AI Agent (rules + LLM) ─┐
→ ML model (recovery %) ├─▶ Repository layer → MongoDB
→ Payment simulator ┘
│
▼
Audit trail (audit_logs)


The ML model will predict `recovery_probability` as a plain number. The
AI agent will consume that number plus payment/customer context and
business rules to choose one of `SMART_RETRY`, `PAYMENT_METHOD_SUGGESTION`,
`REMINDER`, `SUPPORT_ESCALATION`, or `STOP` — the agent decides, the ML
model never picks an action directly. Every automated decision will be
written to `audit_logs` with a reason and confidence score, and guardrails
(max attempts, minimum retry interval, probability floor) will be enforced
before any simulated retry runs.