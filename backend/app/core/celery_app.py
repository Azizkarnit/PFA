from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ins_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.import_tasks",
        "app.tasks.export_tasks",
        "app.tasks.survey_tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Use UTC for all task timestamps to avoid timezone ambiguity
    enable_utc=True,
    timezone="UTC",
    # Retry configuration defaults
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
