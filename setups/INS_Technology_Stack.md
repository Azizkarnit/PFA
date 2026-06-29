# INS Statistical Survey Collection Platform
## Technology Stack & Setup Guide

---

## Component Technologies

### Frontend
- Angular 20
- Angular Material
- Bootstrap 5
- ngx-translate
- ApexCharts

### Backend
- FastAPI
- Pydantic
- SQLAlchemy 2
- Alembic

### Database
- MySQL 8

### Authentication & Security
- JWT (python-jose)
- Passlib + Bcrypt

### Background Processing
- Redis
- Celery
- Celery Beat

### Email Service
- Brevo

### File Handling & Reporting
- OpenPyXL
- Pandas
- WeasyPrint

### Infrastructure
- Docker
- Docker Compose
- Nginx (future deployment)

### Development Tools
- VS Code
- Postman
- MySQL Workbench
- Git
- GitHub

---

## Architecture Overview

```
Angular + Angular Material + Bootstrap + ngx-translate
        ↓
FastAPI + Pydantic + SQLAlchemy + Alembic
        ↓
MySQL
        ↓
Redis + Celery + Celery Beat
        ↓
Brevo
```

---

## Installation & Setup Guide (Windows)

Follow these instructions to download, install, and configure every component required to run this application locally.

### 1. Git (Version Control)
* **Download**: [Git for Windows](https://git-scm.com/download/win)
* **Installation**: Download the installer, run it, and select default options.
* **Verify**: Open PowerShell and run:
  ```powershell
  git --version
  ```

### 2. Node.js & Angular (Frontend Runtime)
* **Download**: [Node.js LTS (v18 or newer recommended)](https://nodejs.org/)
* **Installation**: Run the MSI installer. Ensure the option to add to `PATH` is checked.
* **Verify**:
  ```powershell
  node --version
  npm --version
  ```
* **Install Angular CLI**: Open terminal and run:
  ```powershell
  npm install -g @angular/cli
  ```

### 3. Python (Backend Runtime)
* **Download**: [Python 3.10 or 3.11](https://www.python.org/downloads/)
* **Installation**: 
  > [!IMPORTANT]
  > Check the box that says **"Add python.exe to PATH"** at the bottom of the installer window before clicking Install.
* **Verify**:
  ```powershell
  python --version
  pip --version
  ```

### 4. MySQL Database (via XAMPP or Standalone)
We recommend **XAMPP** for the easiest local MySQL setup:
* **Download**: [XAMPP for Windows](https://www.apachefriends.org/download.html)
* **Installation**: Download and install XAMPP. Select **MySQL** and **phpMyAdmin** during setup.
* **Configuration**:
  1. Open the **XAMPP Control Panel**.
  2. Click **Start** next to **MySQL** (and optionally **Apache** if you want to use the web-based database viewer phpMyAdmin at `http://localhost/phpmyadmin`).
  3. Ensure it runs on the default port `3306` with username `root` and no password.

### 5. Redis (Key-Value Store)
You can set up Redis on Windows in two ways:

#### Option A: Docker (Recommended)
1. Install **Docker Desktop for Windows** from [Docker Desktop](https://www.docker.com/products/docker-desktop). (Make sure to enable WSL2 if prompted during installation).
2. Start Docker Desktop.
3. Start Redis in a container by running:
   ```powershell
   docker run -d --name ins-redis -p 6379:6379 redis:alpine
   ```

#### Option B: Standalone Windows Native Port (No Docker)
If you prefer not to use Docker, you can run Redis directly on Windows:
1. Download the latest native Windows release (`.msi` or `.zip`) from [Github Redis for Windows Port Archive](https://github.com/tporadowski/redis/releases).
2. Install/extract it and double click `redis-server.exe` to run it.
3. Keep the terminal window open.

---

## Quick Start Run Guide

Once everything is installed:

### 1. Initialize Database
In `backend`:
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python create_db.py
alembic upgrade head
python seed.py
python create_test_users.py
```

### 2. Run Backend
In `backend` (with venv active):
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Run Frontend
In `frontend`:
```powershell
cd frontend
npm install
npm run start
```
Go to `http://localhost:4200` to access the application.

