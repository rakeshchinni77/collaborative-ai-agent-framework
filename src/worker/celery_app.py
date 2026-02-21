from celery import Celery
from celery.signals import worker_ready
from src.config import settings
from src.services.logger import get_logger

# Initialize Structured Logger
logger = get_logger("celery_worker")

# Create Celery Application
celery_app = Celery(
    "collaborative_agent_framework",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery Configuration
celery_app.conf.update(
    # Serialization (JSON only for security)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone settings
    timezone="UTC",
    enable_utc=True,

    # Task tracking & reliability
    task_track_started=True,

    # Retry + delivery guarantees
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_acks_on_failure_or_timeout=False,

    # Worker performance tuning
    worker_prefetch_multiplier=1,

    # Result backend settings
    result_expires=3600,

    # Global retry defaults
    task_default_retry_delay=5,  # seconds
    task_annotations={
        "*": {
            "max_retries": 3,
            "autoretry_for": (Exception,),
            "retry_backoff": True,
            "retry_backoff_max": 30,
            "retry_jitter": True,
        }
    },
)


# Task Auto-Discovery
celery_app.autodiscover_tasks(
    packages=["src.worker"],
    related_name="tasks",
)

# Worker Startup Logging
@worker_ready.connect
def on_worker_ready(sender=None, **kwargs):
    """
    Logs a structured JSON entry when the Celery worker is ready.
    Broker credentials are masked for security.
    """
    try:
        broker_host = settings.CELERY_BROKER_URL.split("@")[-1]
    except Exception:
        broker_host = "redis"

    logger.info(
        "Celery worker started",
        extra={
            "service": "celery_worker",
            "broker": broker_host,
        },
    )
