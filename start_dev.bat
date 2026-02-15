@echo off
REM =========================================
REM Trading Backend - VSCode Dev Startup
REM =========================================

REM 1️⃣ Activate virtual environment
call venv\Scripts\activate

REM 2️⃣ Start FastAPI backend
start "FastAPI Backend" cmd /k "echo Starting FastAPI... & uvicorn app.main:app --reload --port 8000"

REM 3️⃣ Start Celery worker
start "Celery Worker" cmd /k "echo Starting Celery Worker... & celery -A app.tasks.celery_app.celery_app worker --loglevel=info --pool=solo"

REM 4️⃣ Start Flower
start "Flower Monitoring" cmd /k "echo Starting Flower... & celery -A app.tasks.celery_app.celery_app flower --port=5555"

REM 5️⃣ Start Mock Price Feed
start "Mock Price Feed" cmd /k "echo Starting Mock Price Feed... & python -c \"from app.tasks.price_tick import mock_price_feed; mock_price_feed('BTCUSDT')\""

echo ======================================
echo All services started!
echo - FastAPI: http://127.0.0.1:8000/docs
echo - Flower: http://127.0.0.1:5555
echo ======================================
pause
