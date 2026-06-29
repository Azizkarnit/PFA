# Complete 2FA Verification and Setup Redis via Docker on Windows

The codebase contains a fully implemented Two-Factor Authentication (2FA) and One-Time Password (OTP) verification module. The backend is configured to use **Redis** to store ephemeral OTP codes, limit OTP resends, and manage temporary 24-hour account locks.

To make local development seamless, we have implemented an **in-memory fallback** in the backend's Redis module. If a local Redis instance or Docker container is not active, the backend will automatically log a warning and fall back to storing OTPs, blacklists, and locks in memory. This means you do not need Docker or Redis installed to run the application for verification.

We also verified the **Brevo Email API** integration. When an OTP is generated, it will be sent to the user's email address using Brevo (via the key configured in the backend's `.env`) and printed to the terminal console using explicit `print()` logs.

---

## Completed Tasks

1. **Redis Fallback System**: Added a robust `InMemoryRedisMock` wrapper inside `backend/app/core/redis.py` that handles connection errors gracefully.
2. **Terminal Output Dispatch**: Enhanced `backend/app/tasks/email_tasks.py` using explicit print statements to display OTP and password reset links in the `uvicorn` console.
3. **Frontend Pages & Resend Action**: Verified the frontend `LoginComponent`, `OTPVerificationComponent` (with translation support, error banners, and resend cooldown action), and `ChangePasswordComponent` are fully built.
4. **Brevo Verification**: Verified the Brevo SMTP key successfully sends emails (verified via a standalone test script returning a 201 status code).

---

## Verification Plan

Perform these steps to run the application locally and verify that the 2FA flow works correctly.

### 1. Database Initialization
1. Ensure your MySQL server (via XAMPP or local installer) is running and listening on port `3306`.
2. Open a terminal, navigate to the `backend` folder, and activate the virtual environment:
   ```powershell
   cd backend
   venv\Scripts\activate
   ```
3. Ensure the database exists:
   ```powershell
   python create_db.py
   ```
4. Run migrations to create the required tables:
   ```powershell
   alembic upgrade head
   ```
5. Seed the database with default settings, roles, and periods:
   ```powershell
   python seed.py
   ```
6. Create the default test accounts (which have `first_login=True` and `two_factor_enabled=True`):
   ```powershell
   python create_test_users.py
   ```

### 2. Start the Backend Server
1. From the same activated `backend` terminal:
   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Monitor the terminal console. You will see both the warning about falling back to in-memory storage (if Redis is not running) and the OTP code dispatch details.

### 3. Start the Frontend Server
1. Open a new terminal, navigate to the `frontend` folder:
   ```powershell
   cd frontend
   npm run start
   ```
2. Open your browser and navigate to `http://localhost:4200`.

### 4. Perform the E2E 2FA Verification Flow
1. Navigate to the login page (`http://localhost:4200/login`).
2. Log in using one of the test users:
   - **Email:** `contact@ins.tn` (or change to your personal email in the DB if you want to receive it in your own inbox)
   - **Password:** `Test@123`
3. Click **Se connecter**.
4. The system will prompt you for 2FA verification and redirect you to `http://localhost:4200/otp`.
5. Check your FastAPI console output in the backend terminal window. You will see:
   ```text
   ========== EMAIL DISPATCH ==========
   To: contact@ins.tn
   Language: fr
   Subject: Votre code de vérification INS
   Body: Your INS Portal code is: XXXXXX
   =====================================
   ```
6. An email will also be sent to that address via Brevo SMTP.
7. Enter this code on the `/otp` page on the frontend and press **Valider**.
8. Since this is your first login, you will be redirected to the password reset page (`/change-password`).
9. Enter a new password to complete the registration flow and access the application dashboard.

