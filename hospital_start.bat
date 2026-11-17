
@echo off
setlocal
title Hospital Equipment Intelligence

set "ROOT=%~dp0"
set "FRONTEND_URL=http://127.0.0.1:5173"
set "BACKEND_URL=http://127.0.0.1:8000"

echo.
echo ==========================================
echo   HOSPITAL EQUIPMENT INTELLIGENCE
echo ==========================================
echo.

REM Check backend environment
if not exist "%ROOT%backend\.venv\Scripts\activate.bat" (
    echo ERROR: Backend virtual environment not found.
    pause
    exit /b 1
)

REM Check frontend project
if not exist "%ROOT%frontend\package.json" (
    echo ERROR: Frontend package.json not found.
    pause
    exit /b 1
)

REM Check Node.js and npm
where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH.
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not available.
    pause
    exit /b 1
)

REM Start backend
echo [1/3] Starting FastAPI backend...

start "Hospital Backend" /D "%ROOT%backend" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

REM Install frontend dependencies if required
echo.
echo [2/3] Checking frontend dependencies...

if not exist "%ROOT%frontend\node_modules" (
    echo Installing frontend packages...
    pushd "%ROOT%frontend"
    call npm install
    if errorlevel 1 (
        echo ERROR: Frontend dependency installation failed.
        popd
        pause
        exit /b 1
    )
    popd
)

REM Start frontend on fixed port
echo.
echo Starting React frontend...

start "Hospital Frontend" /D "%ROOT%frontend" cmd /k "npm run dev -- --host 127.0.0.1 --port 5173 --strictPort"

REM Wait for frontend
echo.
echo [3/3] Waiting for frontend startup...

powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(90); do { Start-Sleep -Seconds 2; try { $r=Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5173' -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } } catch {} } while ((Get-Date) -lt $deadline); exit 1"

if errorlevel 1 (
    echo.
    echo ERROR: Frontend did not respond on port 5173.
    echo Check the Hospital Frontend command window.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   APPLICATION STARTED
echo ==========================================
echo.
echo Frontend: %FRONTEND_URL%
echo Backend:  %BACKEND_URL%
echo API Docs: %BACKEND_URL%/docs
echo.
echo Opening application in browser...

start "" "%FRONTEND_URL%"

echo.
echo Hospital Equipment Intelligence is running.
echo Keep both server windows open.
echo.
pause
