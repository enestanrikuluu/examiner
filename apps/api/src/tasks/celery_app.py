import os
from celery import Celery
from celery.signals import worker_init


@worker_init.connect
def load_all_models(**kwargs):
    """Ensure all SQLAlchemy models are imported so relationships resolve."""
    import src.exams.models  # noqa: F401
    import src.sessions.models  # noqa: F401
    import src.questions.models  # noqa: F401
    import src.users.models  # noqa: F401
    import src.ai.models  # noqa: F401


redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "examiner",
    broker=redis_url,
    backend=redis_url,
    include=[
        "src.tasks.ping",
        "src.tasks.grading",
        "src.tasks.question_generation",
        "src.tasks.isg_generation",
        "src.tasks.export",
        "src.tasks.calibration",
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
        "src.tasks.isg_generation.*": {"queue": "generation"},
        "src.tasks.export.*": {"queue": "export"},
        "src.tasks.calibration.*": {"queue": "calibration"},
    },
    task_default_queue="default",
)
