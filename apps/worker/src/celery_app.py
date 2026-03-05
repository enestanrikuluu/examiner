import os

from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "examiner-worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "src.tasks.ping",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "src.tasks.grading.*": {"queue": "grading"},
        "src.tasks.question_generation.*": {"queue": "generation"},
        "src.tasks.export.*": {"queue": "export"},
        "src.tasks.calibration.*": {"queue": "calibration"},
    },
    task_default_queue="default",
)
