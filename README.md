# INS Statistical Survey Collection & Administrative Tracking Platform

> **Production-grade web application for managing statistical survey lifecycles, administrative directories, asynchronous data collection, and real-time notifications.** Developed for the **National Institute of Statistics (INS) Tunisia**.

---

## 🌟 Key Features

- **Multi-Role Administrative Portal:** Segmented dashboards and permissions for System Administrators, Account Managers, and Survey Managers.
- **Passwordless Survey Respondent Access:** Secure, UUID-based one-time survey token links for external company respondents.
- **Asynchronous Heavy Processing:** Celery worker pipeline processing up to 100MB (~500,000 rows) Excel files with zero main-thread blocking.
- **Staging & Validation Pipeline:** Real-time data staging table with server-side pagination for bulk company imports.
- **Two-Factor Authentication (2FA):** Email-based OTP verification cached in Redis.
- **Real-Time Notifications:** WebSocket notifications powered by Redis Pub/Sub for instant submission and system alerts.
- **Systemic Audit Logging:** Complete event audit trails with background Excel export capabilities.

---

## 🏗️ Architecture Overview

The system uses a modern decoupled architecture:

```
                  ┌─────────────────────────────────────┐
                  │          Angular 21 SPA             │
                  │   Single Page Application Frontend  │
                  └──────────────────┬──────────────────┘
                                     │ HTTP / WebSockets
                                     ▼
                  ┌─────────────────────────────────────┐
                  │         FastAPI REST Engine         │
                  │     OAuth2 / JWT / Security API     │
                  └─────────┬─────────┬─────────┬───────┘
                            │         │         │
               SQLAlchemy   │         │         │ Pub/Sub & Caching
               ORM          │         │         │
                            ▼         │         ▼
         ┌────────────────────┐       │     ┌────────────────────┐
         │    MySQL 8.0 DB    │       │     │    Redis 7 Store   │
         │  Persistent Data   │       │     │ OTP & Notification │
         └────────────────────┘       │     └────────────────────┘
                                      │ Tasks
                                      ▼
                           ┌────────────────────┐
                           │   Celery Workers   │
                           │ Async Background   │
                           └────────────────────┘
```

---

## 🧰 Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** MySQL 8.0 with SQLAlchemy 2.0 ORM & Alembic migrations
- **Task Queue:** Celery with Redis broker
- **Caching & WebSockets:** Redis 7.0 (Pub/Sub)
- **Security:** OAuth2, JWT with JTI blacklisting, Passlib (bcrypt), Rate limiting

### Frontend
- **Framework:** Angular 21 (Standalone Components)
- **UI System:** Angular Material + Custom Design Tokens
- **State & Data:** RxJS Observables, ApexCharts for Analytics
- **Internationalization:** `@ngx-translate` (French, English)

---

## 📁 Repository Structure

```
.
├── backend/                  # FastAPI Application, Celery tasks, and SQLAlchemy models
│   ├── app/                  # Application core, API routes, models, schemas, and tasks
│   ├── migrations/           # Alembic database migration scripts
│   ├── create_admin.py       # Seed script for initial Superadmin user
│   └── seed.py               # Reference data seeder (Roles, Sectors, Periodicity)
├── frontend/                 # Angular 21 Single Page Application
│   └── src/                  # Angular components, services, guards, and assets
├── rapport/                  # Academic LaTeX Report source files & compiled diagrams
├── external_questionnaire/   # Integration specification mock runner
├── docker-compose.yml        # Docker Compose configuration for single-command stack launch
├── ARCHITECTURE.md           # Architecture Decision Records (ADRs) & technical logs
└── COMMANDS.md               # Quick-reference developer command cheat sheet
```

---

## 🚀 Quick Start

### Option A: Running with Docker Compose (Recommended)

To launch the complete application stack (MySQL, Redis, FastAPI Backend, Celery Worker, and Angular Frontend) with a single command:

```bash
docker-compose up --build
```

Access the applications at:
- **Frontend Dashboard:** `http://localhost:4200`
- **Backend API Docs (Swagger):** `http://localhost:8000/docs`

---

### Option B: Local Manual Setup

#### 1. Start Services
Ensure **MySQL** (port 3306) and **Redis** (port 6379) are running on your local system.

#### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MySQL and Redis credentials

# Initialize database schema and seed reference data
python create_db.py
alembic upgrade head
python seed.py
python create_admin.py

# Start FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Start Celery Background Worker (In a separate terminal)
```bash
cd backend
venv\Scripts\activate
celery -A app.core.celery_app worker -P threads -c 4 --loglevel=info
```

#### 4. Frontend Setup (In a separate terminal)
```bash
cd frontend

# Install Node modules
npm install

# Start Angular dev server
npm start
```

---

## 🔑 Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://root@localhost:3306/pfa_db` |
| `SECRET_KEY` | JWT signing secret key | *(Required in production)* |
| `REDIS_URL` | Redis server URL | `redis://localhost:6379/0` |
| `BREVO_API_KEY` | Brevo (Sendinblue) API key for emails | `Optional` |
| `ALLOWED_ORIGINS` | Comma-separated list of CORS origins | `http://localhost:4200` |
| `MAX_UPLOAD_SIZE_MB` | Maximum allowed file upload size | `50` |

---

## 📄 License

This project was developed for the **National Institute of Statistics (INS) Tunisia** as a Graduation Project (PFA). All rights reserved.
