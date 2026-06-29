# INS Platform - Cheat Sheet

Here are the most common commands you'll need while developing the INS project.

## 🚀 Frontend (Angular)
Make sure you are in the `frontend` folder (`cd frontend`).

| Command | Description |
|---|---|
| `ng serve` | Starts the Angular development server (runs on `http://localhost:4200`) |
| `ng build` | Builds the project for production |
| `ng generate component name` | Creates a new Angular component (shortcut: `ng g c name`) |
| `ng generate service name` | Creates a new Angular service (shortcut: `ng g s name`) |

---

## 🐍 Backend (FastAPI & Python)
Make sure you are in the `backend` folder (`cd backend`).

### 1. Starting the Server
| Command | Description |
|---|---|
| `venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` | Starts the FastAPI backend with live-reload enabled |

### 2. Database & Migrations (Alembic)
*Always make sure your XAMPP MySQL server is running before executing these.*

| Command | Description |
|---|---|
| `venv\Scripts\python create_db.py` | Creates the `pfa_db` database if it doesn't exist |
| `venv\Scripts\alembic revision --autogenerate -m "description"` | Generates a new migration file after you change models |
| `venv\Scripts\alembic upgrade head` | Applies any pending migrations to your database |
| `venv\Scripts\alembic current` | Shows the current migration state |
| `venv\Scripts\alembic check` | Checks if there are any model changes that haven't been migrated |

### 3. Utility Scripts
| Command | Description |
|---|---|
| `venv\Scripts\python seed.py` | Seeds the database with default roles, settings, and periodicity |
| `venv\Scripts\python create_admin.py` | Creates the test system admin user (`admin@ins.tn`) |

---

## 💻 Virtual Environment (venv)
If your terminal doesn't automatically activate the virtual environment:

| Command | Description |
|---|---|
| `venv\Scripts\activate` | Activates the Python virtual environment |
| `deactivate` | Exits the virtual environment |
