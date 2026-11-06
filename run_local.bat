@echo off
REM NexusAgent Enterprise - Windows CMD Launcher
echo ===================================================
echo   NexusAgent Enterprise Platform - CMD Launcher
echo ===================================================

where docker >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Docker detected. Starting full stack via Docker Compose...
    docker compose up --build
    goto :eof
)

echo [WARN] Docker not found in PATH. Launching local services in separate CMD windows...
start "Nexus MCP Server (8080)" cmd /k "cd services\mcp_server && python -m venv venv && call venv\Scripts\activate && pip install -r requirements.txt && python server.py"
start "Nexus Backend (8000)" cmd /k "cd services\backend && set MCP_SERVER_URL=http://localhost:8080 && set DATABASE_URL=postgresql://nexusadmin:nexusstrongpassword123@localhost:5432/nexusagent_db && python -m venv venv && call venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
start "Nexus Django Admin (8001)" cmd /k "cd services\django_app && set DB_HOST=localhost && python -m venv venv && call venv\Scripts\activate && pip install -r requirements.txt && python manage.py migrate && python manage.py runserver 0.0.0.0:8001"
start "Nexus Frontend (3000)" cmd /k "cd services\frontend && npm install && npm run dev"
