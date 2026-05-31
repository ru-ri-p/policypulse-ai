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

# MENA law-focused spiders (UTC) — before EU/US daily runs
_MENA_SPIDERS = (
    ("uae_legislation", 6, 0),
    ("dfsa_rulebook", 6, 15),
    ("difc_laws", 6, 30),
    ("adgm_fsra", 6, 45),
    ("sdaia_saudi", 7, 0),
    ("uae_ai_office", 7, 15),
    ("digital_dubai", 7, 30),
)

app.conf.beat_schedule = {
    **{
        f"scrape-mena-{name}-daily": {
            "task": "ingestion.tasks.run_spider",
            "schedule": crontab(hour=hour, minute=minute),
            "args": (name,),
        }
        for name, hour, minute in _MENA_SPIDERS
    },
    "retag-after-mena-scrape": {
        "task": "ingestion.tasks.retag_all_documents",
        "schedule": crontab(hour=7, minute=50),
    },
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
