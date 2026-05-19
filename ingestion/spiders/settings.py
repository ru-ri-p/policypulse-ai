# ingestion/spiders/settings.py
BOT_NAME = "policypulse"

SPIDER_MODULES = ["spiders.spiders"]
NEWSPIDER_MODULE = "spiders.spiders"

USER_AGENT = "PolicyPulse Research Bot 1.0 (academic/research use)"

ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

CONCURRENT_REQUESTS_PER_DOMAIN = 1
RETRY_TIMES = 2

ITEM_PIPELINES = {
    "spiders.pipelines.PostgresPipeline": 300,
    # MLPipeline is slow (loads two transformer models per page). Re-enable when needed:
    # "spiders.pipelines.MLPipeline": 400,
}

FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"
