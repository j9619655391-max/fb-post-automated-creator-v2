@echo off
setlocal
cd /d "%~dp0"
docker-compose ps
echo.
echo API root:
curl.exe --max-time 10 -I http://127.0.0.1:8000/
echo.
echo Celery worker:
docker exec fb-post-app-celery celery -A app.scheduler inspect ping --timeout=5
endlocal
