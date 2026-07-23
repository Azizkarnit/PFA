@echo off
echo ===================================================
echo   INS External Questionnaire System Bootstrapper
echo ===================================================
echo.

cd backend

IF NOT EXIST venv (
    echo [1/3] Creating virtual environment (venv)...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Failed to create virtual environment. 
        echo Please ensure Python is installed and added to your system environment variables (PATH).
        echo.
        pause
        exit /b %ERRORLEVEL%
    )
)

echo [2/3] Installing dependencies from requirements.txt...
call venv\Scripts\activate.bat
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to install dependencies. 
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] Starting uvicorn server on http://localhost:3000...
echo.
python -m uvicorn app.main:app --port 3000 --reload
pause
