@echo off
setlocal
cd /d "%~dp0"
if not exist "backend\.venv\Scripts\python.exe" (
  py -3 -m venv backend\.venv
)
call backend\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
start "Hospital API" cmd /k "cd /d ""%~dp0backend"" && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
if not exist "frontend\node_modules" (
  cd frontend
  call npm install
  cd ..
)
start "Hospital Web App" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 127.0.0.1"
timeout /t 4 >nul
start "" http://127.0.0.1:5173
endlocal
