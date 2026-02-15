from celery import Celery

celery_app = Celery(
    "trading_engine",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# ✅ DO NOT import strategy_runner here
# We'll let tasks import celery_app instead
# Auto-discover all tasks in the tasks folder
celery_app.autodiscover_tasks(["app.tasks"])