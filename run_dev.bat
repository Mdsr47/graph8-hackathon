@echo off
echo ===================================================
echo Starting graph8 Self-Healing Outbound Agent (Fullstack)
echo ===================================================
start "graph8 Backend (FastAPI)" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
start "graph8 Frontend (Vite)" cmd /k "cd frontend && npm.cmd run dev"
echo.
echo ===================================================
echo Backend running at:  http://localhost:8000
echo Frontend running at: http://localhost:5173
echo ===================================================
