# Platform System Architecture & Engineering Decisions

This document details the architectural decisions, design patterns, security controls, and resolution logs for the INS Statistical Survey Collection Platform.

---

## 🏛️ System Architecture Overview

The system is designed as a decoupled, multi-tier web platform tailored for statistical survey collection, bulk data management, and real-time monitoring.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client Browser Layer                           │
│                       Angular 21 SPA (RxJS, Material)                   │
└───────────────────┬─────────────────────────────────┬───────────────────┘
                    │ REST API (JSON / JWT)           │ WebSockets (WS)
                    ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend Service                       │
│              OAuth2 / JWT • Security Middleware • Router v1             │
└─────────┬───────────────────┬───────────────────┬───────────────────────┘
          │ ORM (SQLAlchemy)  │ Task Dispatch     │ Pub/Sub
          ▼                   ▼                   ▼
┌───────────────────┐ ┌───────────────────┐ ┌─────────────────────────────┐
│   MySQL 8.0 DB    │ │  Celery Workers   │ │      Redis 7 Data Store     │
│ Persistent Data   │ │ (Async Pipelines) │ │ OTP Caching • WebSocket Bus │
└───────────────────┘ └───────────────────┘ └─────────────────────────────┘
```

---

## 📋 Architectural Decisions (ADR)

### ADR-001: Asynchronous Processing for Large Datasets
- **Context:** Uploading 100MB Excel files (~500,000 rows) or exporting massive audit logs synchronously blocked FastAPI event loops and froze the UI.
- **Decision:** Shift heavy processing to Celery workers using Redis as the task broker.
- **Pattern:**
  1. API receives file, saves to `uploads/`, and immediately returns a `session_id`.
  2. Celery worker thread parses chunks (2,000 rows at a time) and populates `company_import_staging`.
  3. Frontend polls session progress and uses **server-side pagination** to present staging rows with fluid 60fps scrolling.

### ADR-002: Threaded Concurrency for Task Queue
- **Context:** Single-threaded workers (`--pool=solo`) caused small tasks (e.g., 5KB files) to block behind large imports (100MB files).
- **Decision:** Execute Celery with multi-threaded pools:
  ```bash
  celery -A app.core.celery_app worker -P threads -c 4 --loglevel=info
  ```
- **Outcome:** 4 concurrent thread workers process small and large background jobs simultaneously.

### ADR-003: UUID-Based Token Model for External Questionnaires
- **Context:** External company respondents require access to specific survey passages without account creation or password management.
- **Decision:** Generate 128-bit UUID v4 tokens representing a `(Contact × Passage)` pair.
- **Rationale:**
  - Opaque: Carries no embedded user payload (unlike JWT).
  - Collision-Free: Enables safe server-to-server validation between INS platform and external questionnaire systems.
  - Granular: One user filling 3 survey passages receives 3 distinct tokens.

### ADR-004: Role-Bounded Real-Time Notification Pipeline
- **Context:** Account Managers were receiving survey submission notifications, creating dashboard noise.
- **Decision:** Filter notification recipients at the SQL level based on role domain:
  - `SURVEY_MANAGER` & `SYSTEM_ADMINISTRATOR`: Receive collection & submission alerts.
  - `ACCOUNT_MANAGER`: Excluded from collection alerts; receives account lockouts & company directory updates.

---

## 🔒 Security Architecture Controls

1. **Authentication:** OAuth2 with JWT access tokens.
2. **Two-Factor Authentication (2FA):** Passwordless OTP sent via email (Brevo) with 5-minute Redis expiration.
3. **Rate Limiting:** IP-based rate limiting on authentication endpoints (max 20 attempts / 15 mins).
4. **Token Revocation:** Active token blacklisting in Redis upon user logout (`jti` claim tracking).
5. **Request Guards:** Upload size limit middleware enforcing configurable `MAX_UPLOAD_SIZE_MB`.
