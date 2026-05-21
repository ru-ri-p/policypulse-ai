# infra/celery_app.py
from celery import Celery
from celery.schedules import crontab

app = Celery(
    "policypulse",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["ingestion.tasks"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

app.conf.beat_schedule = {
    "scrape-eu-ai-act-daily": {
        "task": "ingestion.tasks.run_spider",
        "schedule": crontab(hour=9, minute=0),
        "args": ("eu_ai_act",),
    },
    "scrape-federal-register-daily": {
        "task": "ingestion.tasks.run_spider",
        "schedule": crontab(hour=9, minute=30),
        "args": ("federal_register",),
    },
    "scrape-nist-daily": {
        "task": "ingestion.tasks.run_spider",
        "schedule": crontab(hour=10, minute=0),
        "args": ("nist_airc",),
    },
    "scrape-ico-uk-daily": {
        "task": "ingestion.tasks.run_spider",
        "schedule": crontab(hour=10, minute=30),
        "args": ("ico_uk",),
    },
    "process-pending-ml-daily": {
        "task": "ingestion.tasks.process_pending_documents",
        "schedule": crontab(hour=11, minute=0),
        "kwargs": {"limit": 100},
    },
    "generate-pending-digests-daily": {
        "task": "ingestion.tasks.generate_pending_digests",
        "schedule": crontab(hour=12, minute=0),
        "kwargs": {"limit": 50},
    },
    "nightly-relevance-alerts": {
        "task": "ingestion.tasks.run_nightly_relevance_alerts",
        "schedule": crontab(hour=7, minute=0),
        "kwargs": {"hours": 24},
    },
}
