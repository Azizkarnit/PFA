# Specification for External Questionnaire System

This document specifies the architecture, database schema, backend API endpoints, and frontend layout required to build the **External Questionnaire System**. 

Provide this file to the AI coding agent assigned to build the external system.

---

## 🚀 Prompt for the Building Agent
> **"Build a standalone Questionnaire System (FastAPI backend + HTML/JS/Vanilla CSS frontend) based on the database schemas, API specs, and frontend page flows detailed in the attached `EXTERNAL_SYSTEM_SPECIFICATION.md` document. The system must authenticate server-to-server with the main PFA Platform using the defined API key structure and must support a no-login, save-and-resume questionnaire workflow keyed by a UUID token."**

---

## 📐 Overall Architecture & Context

The external system has **no user accounts, logins, or navigation menus**. 
Access is granted entirely via a unique `uuid` parameter in the URL.

```
                  ┌──────────────────────────────────────────────┐
                  │                 PFA Backend                  │
                  └──────────────┬────────────────▲──────────────┘
                                 │                │
            POST /ext/resolve    │                │ POST /ext/status-update
            (validate UUID,      │                │ (mark IN_PROGRESS/COMPLETED)
            get questions)       │                │
                                 ▼                │
                  ┌───────────────────────────────┴──────────────┐
                  │               External Backend               │
                  │              (FastAPI Service)               │
                  └──────┬────────────────────────▲──────────────┘
                         │                        │
         Session &       │                        │ POST /session/open
         Saved Answers   │                        │ PATCH /session/save
                         ▼                        │ POST /session/submit
                  ┌───────────────────────────────┴──────────────┐
                  │              External Frontend               │
                  │             (HTML / Vanilla CSS)             │
                  └──────────────────────────────────────────────┘
```

---

## 💾 Database Schema (PostgreSQL / SQLite)

The external system uses two database tables to track sessions and save answers.

### 1. `ext_sessions`
Tracks the questionnaire session status. One row per UUID.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `uuid` | VARCHAR(36) | PRIMARY KEY | The UUID token received from PFA |
| `passage_id` | INTEGER | NOT NULL | Caches the passage ID from PFA |
| `company_id` | INTEGER | NOT NULL | Caches the company ID from PFA |
| `closing_date` | TIMESTAMP | NOT NULL | Caches the closing date from PFA |
| `status` | VARCHAR(20) | NOT NULL | `IN_PROGRESS` or `SUBMITTED` |
| `started_at` | TIMESTAMP | DEFAULT NOW() | When the session was first opened |
| `last_saved_at` | TIMESTAMP | NULL | When the session was last saved |
| `submitted_at` | TIMESTAMP | NULL | When the final submission occurred |

### 2. `ext_responses`
Stores responses entered by users.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | SERIAL | PRIMARY KEY | Unique ID |
| `session_uuid` | VARCHAR(36) | Foreign Key → `ext_sessions.uuid` | The session this answer belongs to |
| `question_id` | INTEGER | NOT NULL | The PFA-supplied ID of the question |
| `value_text` | TEXT | NULL | Holds string values (for text questions) |
| `value_number` | NUMERIC | NULL | Holds float/int values (for numeric questions) |
| `saved_at` | TIMESTAMP | DEFAULT NOW() | Timestamp of last save |

* **Unique Constraint**: `(session_uuid, question_id)` (ensures one answer per question per session).

---

## ⚙️ Configuration (`.env`)

```ini
PORT=3000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ext_questionnaire_db
PFA_API_URL=http://localhost:8000
EXT_TO_PFA_API_KEY=dev_ext_to_pfa_secret_key
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## ⚙️ Backend Endpoints (FastAPI)

### 1. Open Session
* **Path**: `POST /session/open`
* **Body**:
  ```json
  { "uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479" }
  ```
* **Logic**:
  1. Call PFA Backend: `POST {PFA_API_URL}/api/v1/ext/resolve`
     * Headers: `X-Api-Key: {EXT_TO_PFA_API_KEY}`
     * Body: `{ "uuid": "{uuid}" }`
  2. If PFA returns `404` or `400` (e.g., passage closed), return that exact error.
  3. Otherwise, check if a row exists in `ext_sessions` for this `uuid`.
     * **If not found**: Create a new session row in `ext_sessions` (caching `passage_id`, `company_id`, `closing_date`, setting `status` to `IN_PROGRESS`).
     * **If found**: Retrieve all saved responses from `ext_responses`.
  4. Return the survey details, questions list, session status, and any saved responses.
* **Response**:
  ```json
  {
    "survey_name": "Enquête Annuelle 2026",
    "company_name": "Acme Corp",
    "closing_date": "2026-12-31T23:59:00",
    "status": "IN_PROGRESS",
    "questions": [
      { "id": 1, "order": 1, "text": "Chiffre d'affaires annuel (DZD)", "type": "NUMBER", "required": true },
      { "id": 2, "order": 2, "text": "Nombre d'employés", "type": "NUMBER", "required": true },
      { "id": 3, "order": 3, "text": "Commentaires", "type": "TEXT", "required": false }
    ],
    "saved_responses": {
      "1": { "value_number": 5000000 },
      "2": { "value_number": 42 }
    }
  }
  ```

### 2. Save Draft (Autosave / Manual Save)
* **Path**: `PATCH /session/save`
* **Headers**: `X-UUID: f47ac10b-58cc-4372-a567-0e02b2c3d479`
* **Body**:
  ```json
  {
    "answers": [
      { "question_id": 1, "value_number": 5500000 },
      { "question_id": 3, "value_text": "Updated comments here" }
    ]
  }
  ```
* **Logic**:
  1. Retrieve session matching `X-UUID`. Check if `closing_date` has passed. If yes, reject with `400 Bad Request`.
  2. Upsert answers in `ext_responses` table mapping to `session_uuid`.
  3. Update `ext_sessions.last_saved_at` to `now()`.
  4. Notify PFA Backend: `POST {PFA_API_URL}/api/v1/ext/status-update`
     * Headers: `X-Api-Key: {EXT_TO_PFA_API_KEY}`
     * Body: `{ "uuid": "{uuid}", "status": "IN_PROGRESS" }`
  5. Return success.
* **Response**: `{ "message": "Draft saved successfully" }`

### 3. Final Submission
* **Path**: `POST /session/submit`
* **Headers**: `X-UUID: f47ac10b-58cc-4372-a567-0e02b2c3d479`
* **Body**:
  ```json
  {
    "answers": [
      { "question_id": 1, "value_number": 5500000 },
      { "question_id": 2, "value_number": 45 },
      { "question_id": 3, "value_text": "Final submit" }
    ]
  }
  ```
* **Logic**:
  1. Retrieve session. Reject with `400` if `closing_date` has passed.
  2. Validate that all `required: true` questions are answered. Return list of validation errors if empty.
  3. Save/overwrite all answers in `ext_responses`.
  4. Update `ext_sessions.status` to `SUBMITTED`, set `submitted_at` to `now()`.
  5. Notify PFA Backend: `POST {PFA_API_URL}/api/v1/ext/status-update`
     * Headers: `X-Api-Key: {EXT_TO_PFA_API_KEY}`
     * Body: `{ "uuid": "{uuid}", "status": "COMPLETED", "submitted_at": "{now()}" }`
  6. Return success.
* **Response**: `{ "message": "Questionnaire submitted successfully" }`

---

## 🎨 Frontend Specifications (HTML, Vanilla CSS & Vanilla JS)

Build a clean, responsive single-page application. Ensure the UI looks clean and uses modern, cohesive palettes (e.g., deep blue theme matching the main platform).

### States & Views

#### 1. Loading State
* Rendered on page load when reading `?uuid=` from the URL.
* Visual: A clean loading spinner and message: *"Loading questionnaire..."*.

#### 2. Error Screen
* Triggered if the UUID is missing, invalid, or database call fails.
* Visual: Red error alert card. Message matches API failure (e.g., *"This questionnaire has closed"* or *"Invalid link"*).

#### 3. Interactive Form Screen
* Displays Survey Name, Company name, and closing date/deadline banner prominently at the top.
* Dynamically loops over the `questions` array and renders input fields:
  * `NUMBER` type -> Render `<input type="number">`
  * `TEXT` type -> Render `<textarea>`
  * `SELECT` type -> Render `<select>`
  * `BOOLEAN` type -> Render yes/no radio buttons or a checkbox
* Pre-populates all inputs using the keys/values returned in `saved_responses`.
* **Action Buttons**:
  * **"Save Draft"**: Calls `PATCH /session/save`. Shows a toast message *"Draft saved successfully"* with timestamp.
  * **"Submit Questionnaire"**: Calls `POST /session/submit`. Warns user if required fields are missing.
* **Read-only Lock**:
  * If the session response `status` is `SUBMITTED`, or the current time exceeds `closing_date`, disable all inputs, checkboxes, and buttons.
  * Render a banner: *"Completed: This survey was submitted on [date] and is read-only"* OR *"Closed: This survey closed on [date] and is read-only"*.

#### 4. Success Screen
* Rendered upon successful submission.
* Visual: Large green success checkmark.
* Message: *"Thank you! Your questionnaire responses have been securely submitted to the INS. You may close this tab or print a record of your responses."*
* Include a **"Print Summary"** button to trigger `window.print()` to allow the company to keep a physical/PDF record of what they entered.
