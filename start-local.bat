@echo off
setlocal
cd /d "%~dp0"
if not exist .env (
  echo Missing .env. Copy .env.example to .env and configure local settings first.
  exit /b 1
)
echo Starting PostgreSQL, Redis, API, Celery Worker, and Celery Beat...
docker-compose up -d
echo.
docker-compose ps
endlocal
