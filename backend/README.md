# INS Platform Backend — FastAPI Service

The backend is an asynchronous, high-performance RESTful API built with **FastAPI**, **SQLAlchemy**, **MySQL**, **Redis**, and **Celery**.

---

## 🏗️ Architecture & Stack

- **Framework:** FastAPI (Python 3.11+)
- **Database ORM:** SQLAlchemy 2.0 + Alembic (Migrations)
- **Database Driver:** PyMySQL + MySQL 8.0
- **Asynchronous Task Queue:** Celery (Worker threads)
- **Cache & Message Broker:** Redis (OTP caching, Session management, WebSockets Pub/Sub)
- **Authentication:** OAuth2 JWT + Passwordless OTP 2FA

---

## 📁 Directory Structure

```
backend/
├── app/
│   ├── api/             # API Router definitions & endpoints (v1)
│   ├── core/            # Security, database connection, Redis, Celery, WebSockets
│   ├── models/          # SQLAlchemy Database Models
│   ├── schemas/         # Pydantic validation schemas
│   ├── tasks/           # Celery background tasks (imports, emails, exports)
│   └── main.py          # FastAPI Application Entrypoint
├── migrations/          # Alembic database migrations
├── create_db.py         # Utility: Auto-create MySQL database
├── seed.py              # Utility: Seed initial database tables and reference data
├── create_admin.py      # Utility: Create initial superadmin user
├── requirements.txt     # Python dependencies
└── Dockerfile           # Production container build definition
```

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.11 or higher
- MySQL Server 8.0+ running on `localhost:3306`
- Redis Server 7.0+ running on `localhost:6379`

### 2. Environment Configuration
Copy the example environment configuration:
```bash
cp .env.example .env
```
Edit `.env` to match your local database and credentials:
```ini
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/pfa_db
SECRET_KEY=your_secure_random_key
REDIS_URL=redis://localhost:6379/0
```

### 3. Virtual Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux / macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Database Setup & Migrations
```bash
# Create database (if not exists)
python create_db.py

# Run Alembic migrations to apply full database schema
alembic upgrade head

# Seed reference data (Roles, Periodicity, Sectors)
python seed.py

# Create initial System Administrator account
python create_admin.py
```

### 5. Running the Backend Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Access the interactive OpenAPI / Swagger documentation at: **`http://localhost:8000/docs`**

---

## ⚙️ Running Background Tasks (Celery)

Heavy processing (Excel parsing up to 100MB, email dispatch, data exports) runs via Celery worker threads.

To launch a Celery worker:
```bash
celery -A app.core.celery_app worker -P threads -c 4 --loglevel=info
```

---

## 🧪 Testing

Run pytest for automated endpoint and model testing:
```bash
pytest
```
